"""
测试用户注册和登录
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

print("=" * 50)
print("测试1：注册用户")
print("=" * 50)

# 注册
register_data = {
    "username": "testuser",
    "password": "123456",
    "email": "test@example.com"
}

response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

print("\n" + "=" * 50)
print("测试2：用户登录")
print("=" * 50)

# 登录（使用 OAuth2 表单格式）
login_data = {
    "username": "testuser",
    "password": "123456"
}

response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
print(f"状态码: {response.status_code}")
result = response.json()
print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

if "access_token" in result:
    token = result["access_token"]
    print(f"\n✅ Token: {token[:50]}...")
    
    # 测试受保护的接口（需要先实现）
    print("\n" + "=" * 50)
    print("测试3：验证 Token（需要实现受保护接口）")
    print("=" * 50)
    print("Token 获取成功，可以用于后续请求")
else:
    print("\n❌ 登录失败")
