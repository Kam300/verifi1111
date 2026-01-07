# SheerID 验证配置文件 - Perplexity.ai

# SheerID API 配置
PROGRAM_ID = '681d40e03e7a8077098cb1b6'
SHEERID_BASE_URL = 'https://services.sheerid.com'
MY_SHEERID_URL = 'https://my.sheerid.com'

# 文件大小限制
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

# 学校配置 - Pennsylvania State University 多校区
SCHOOLS = {
    '2565': {
        'id': 2565,
        'idExtended': '2565',
        'name': 'Pennsylvania State University-Main Campus',
        'city': 'University Park',
        'state': 'PA',
        'country': 'US',
        'type': 'UNIVERSITY',
        'domain': 'PSU.EDU',
        'latitude': 40.798214,
        'longitude': -77.85991
    },
    '651379': {
        'id': 651379,
        'idExtended': '651379',
        'name': 'Pennsylvania State University-World Campus',
        'city': 'University Park',
        'state': 'PA',
        'country': 'US',
        'type': 'UNIVERSITY',
        'domain': 'PSU.EDU',
        'latitude': 40.832783,
        'longitude': -77.84159
    },
    '8387': {
        'id': 8387,
        'idExtended': '8387',
        'name': 'Pennsylvania State University-Penn State Harrisburg',
        'city': 'Middletown',
        'state': 'PA',
        'country': 'US',
        'type': 'UNIVERSITY',
        'domain': 'PSU.EDU',
        'latitude': 40.204082,
        'longitude': -76.74168
    },
    '8382': {
        'id': 8382,
        'idExtended': '8382',
        'name': 'Pennsylvania State University-Penn State Altoona',
        'city': 'Altoona',
        'state': 'PA',
        'country': 'US',
        'type': 'UNIVERSITY',
        'domain': 'PSU.EDU',
        'latitude': 40.54092,
        'longitude': -78.40825
    },
    '8396': {
        'id': 8396,
        'idExtended': '8396',
        'name': 'Pennsylvania State University-Penn State Berks',
        'city': 'Reading',
        'state': 'PA',
        'country': 'US',
        'type': 'UNIVERSITY',
        'domain': 'PSU.EDU',
        'latitude': 40.359947,
        'longitude': -75.97615
    },
}

# 默认学校
DEFAULT_SCHOOL_ID = '2565'

# UTM 参数（营销追踪参数）
DEFAULT_UTM_PARAMS = {
    'utm_source': 'perplexity',
    'utm_medium': 'student',
    'utm_campaign': 'student_discount'
}
