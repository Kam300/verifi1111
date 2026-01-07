"""SheerID 学生验证主程序 - Perplexity.ai"""
import re
import random
import logging
import httpx
from typing import Dict, Optional, Tuple

from . import config
from .name_generator import NameGenerator, generate_birth_date
from .img_generator import generate_image, generate_psu_email

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class SheerIDVerifier:
    """SheerID 学生身份验证器 - Perplexity"""

    def __init__(self, install_page_url: str, verification_id: Optional[str] = None):
        self.install_page_url = self.normalize_url(install_page_url)
        self.verification_id = verification_id
        self.external_user_id = self.parse_external_user_id(self.install_page_url)
        self.device_fingerprint = self._generate_device_fingerprint()
        self.http_client = httpx.Client(timeout=30.0)

    def __del__(self):
        if hasattr(self, "http_client"):
            self.http_client.close()

    @staticmethod
    def _generate_device_fingerprint() -> str:
        chars = '0123456789abcdef'
        return ''.join(random.choice(chars) for _ in range(32))

    @staticmethod
    def normalize_url(url: str) -> str:
        """规范化 URL（保留原样）"""
        return url

    @staticmethod
    def parse_verification_id(url: str) -> Optional[str]:
        """从 URL 中解析 verificationId"""
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def parse_external_user_id(url: str) -> Optional[str]:
        """从 URL 中解析 externalUserId"""
        match = re.search(r"externalUserId=([a-f0-9\-]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def create_verification(self) -> str:
        """通过 installPageUrl 申请新的 verificationId"""
        body = {
            "programId": config.PROGRAM_ID,
            "installPageUrl": self.install_page_url,
        }
        data, status = self._sheerid_request(
            "POST", f"{config.MY_SHEERID_URL}/rest/v2/verification/", body
        )
        if status != 200 or not isinstance(data, dict) or not data.get("verificationId"):
            raise Exception(f"创建 verification 失败 (状态码 {status}): {data}")

        self.verification_id = data["verificationId"]
        logger.info(f"✅ 获取 verificationId: {self.verification_id}")
        return self.verification_id

    def _sheerid_request(
        self, method: str, url: str, body: Optional[Dict] = None
    ) -> Tuple[Dict, int]:
        """发送 SheerID API 请求"""
        headers = {
            "Content-Type": "application/json",
        }

        try:
            response = self.http_client.request(
                method=method, url=url, json=body, headers=headers
            )
            try:
                data = response.json()
            except Exception:
                data = response.text
            return data, response.status_code
        except Exception as e:
            logger.error(f"SheerID 请求失败: {e}")
            raise

    def _upload_to_s3(self, upload_url: str, img_data: bytes) -> bool:
        """上传 PNG 到 S3"""
        try:
            headers = {"Content-Type": "image/png"}
            response = self.http_client.put(
                upload_url, content=img_data, headers=headers, timeout=60.0
            )
            return 200 <= response.status_code < 300
        except Exception as e:
            logger.error(f"S3 上传失败: {e}")
            return False

    def verify(
        self,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        birth_date: str = None,
        school_id: str = None,
    ) -> Dict:
        """执行验证流程"""
        try:
            current_step = "initial"

            if not first_name or not last_name:
                name = NameGenerator.generate()
                first_name = name["first_name"]
                last_name = name["last_name"]

            school_id = school_id or config.DEFAULT_SCHOOL_ID
            school = config.SCHOOLS[school_id]

            if not email:
                email = generate_psu_email(first_name, last_name)
            if not birth_date:
                birth_date = generate_birth_date()

            # 如果没有 verification_id，先创建一个
            if not self.verification_id:
                logger.info("申请新的 verificationId ...")
                self.create_verification()

            logger.info(f"学生信息: {first_name} {last_name}")
            logger.info(f"邮箱: {email}")
            logger.info(f"学校: {school['name']}")
            logger.info(f"生日: {birth_date}")
            logger.info(f"验证 ID: {self.verification_id}")

            # 生成学生证 PNG
            logger.info("步骤 1/4: 生成学生证 PNG...")
            img_data = generate_image(first_name, last_name, school_id)
            file_size = len(img_data)
            logger.info(f"✅ PNG 大小: {file_size / 1024:.2f}KB")

            # 提交学生信息
            logger.info("步骤 2/4: 提交学生信息...")
            step2_body = {
                "firstName": first_name,
                "lastName": last_name,
                "birthDate": birth_date,
                "email": email,
                "phoneNumber": "",
                "organization": {
                    "id": int(school_id),
                    "idExtended": school["idExtended"],
                    "name": school["name"],
                },
                "deviceFingerprintHash": self.device_fingerprint,
                "locale": "en-US",
                "metadata": {
                    "marketConsentValue": False,
                    "refererUrl": self.install_page_url,
                    "verificationId": self.verification_id,
                    "flags": '{"collect-info-step-email-first":"default","doc-upload-considerations":"default","doc-upload-may24":"default","doc-upload-redesign-use-legacy-message-keys":false,"docUpload-assertion-checklist":"default","font-size":"default","include-cvec-field-france-student":"not-labeled-optional"}',
                    "submissionOptIn": "By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount",
                },
            }

            step2_data, step2_status = self._sheerid_request(
                "POST",
                f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/collectStudentPersonalInfo",
                step2_body,
            )

            if step2_status != 200:
                raise Exception(f"步骤 2 失败 (状态码 {step2_status}): {step2_data}")
            if step2_data.get("currentStep") == "error":
                error_msg = ", ".join(step2_data.get("errorIds", ["Unknown error"]))
                raise Exception(f"步骤 2 错误: {error_msg}")

            logger.info(f"✅ 步骤 2 完成: {step2_data.get('currentStep')}")
            current_step = step2_data.get("currentStep", current_step)

            # 跳过 SSO（如需要）
            if current_step in ["sso", "collectStudentPersonalInfo"]:
                logger.info("步骤 3/4: 跳过 SSO 验证...")
                step3_data, _ = self._sheerid_request(
                    "DELETE",
                    f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/sso",
                )
                logger.info(f"✅ 步骤 3 完成: {step3_data.get('currentStep')}")
                current_step = step3_data.get("currentStep", current_step)

            # 上传文档并完成提交
            logger.info("步骤 4/4: 请求并上传文档...")
            step4_body = {
                "files": [
                    {"fileName": "student_card.png", "mimeType": "image/png", "fileSize": file_size}
                ]
            }
            step4_data, step4_status = self._sheerid_request(
                "POST",
                f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/docUpload",
                step4_body,
            )
            if not step4_data.get("documents"):
                raise Exception("未能获取上传 URL")

            upload_url = step4_data["documents"][0]["uploadUrl"]
            logger.info("✅ 获取上传 URL 成功")
            if not self._upload_to_s3(upload_url, img_data):
                raise Exception("S3 上传失败")
            logger.info("✅ 学生证上传成功")

            step6_data, _ = self._sheerid_request(
                "POST",
                f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/completeDocUpload",
            )
            logger.info(f"✅ 文档提交完成: {step6_data.get('currentStep')}")
            final_status = step6_data

            # 返回等待审核状态
            return {
                "success": True,
                "pending": True,
                "message": "文档已提交，等待审核",
                "verification_id": self.verification_id,
                "redirect_url": final_status.get("redirectUrl"),
                "status": final_status,
            }

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return {"success": False, "message": str(e), "verification_id": self.verification_id}


def main():
    """主函数 - 命令行界面"""
    import sys

    print("=" * 60)
    print("SheerID Perplexity 学生身份验证工具 (Python版)")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("请输入 SheerID 验证 URL: ").strip()

    if not url:
        print("❌ 错误: 未提供 URL")
        sys.exit(1)

    verification_id = SheerIDVerifier.parse_verification_id(url)
    verifier = SheerIDVerifier(url, verification_id=verification_id)

    print(f"👉 使用链接: {verifier.install_page_url}")
    if verifier.verification_id:
        print(f"已解析 verificationId: {verifier.verification_id}")
    if verifier.external_user_id:
        print(f"externalUserId: {verifier.external_user_id}")
    print()

    result = verifier.verify()

    print()
    print("=" * 60)
    print("验证结果:")
    print("=" * 60)
    print(f"状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"消息: {result['message']}")
    if result.get("redirect_url"):
        print(f"跳转 URL: {result['redirect_url']}")
    print("=" * 60)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())
