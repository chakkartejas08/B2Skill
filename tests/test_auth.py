def _register(client, role="student", email="test@example.com", business_name=""):
    return client.post(
        "/auth/register",
        data={
            "role": role,
            "full_name": "Test User",
            "email": email,
            "phone": "",
            "password": "password123",
            "confirm_password": "password123",
            "business_name": business_name,
        },
        follow_redirects=True,
    )


def test_student_registration_creates_profile(client, app):
    resp = _register(client, role="student", email="student1@example.com")
    assert resp.status_code == 200

    with app.app_context():
        from app.models.user import User

        user = User.query.filter_by(email="student1@example.com").first()
        assert user is not None
        assert user.is_student()
        assert user.student_profile is not None


def test_business_registration_requires_business_name(client):
    resp = _register(client, role="business", email="biz1@example.com", business_name="")
    assert b"Business name is required" in resp.data


def test_login_with_wrong_password_fails(client):
    _register(client, role="student", email="student2@example.com")
    resp = client.post(
        "/auth/login",
        data={"email": "student2@example.com", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert b"Incorrect email or password" in resp.data


def test_business_route_blocked_for_student(client):
    _register(client, role="student", email="student3@example.com")
    resp = client.get("/business/dashboard")
    assert resp.status_code == 403


def test_admin_route_blocked_for_anonymous(client):
    resp = client.get("/admin/dashboard")
    # redirected to login since not authenticated
    assert resp.status_code in (302, 401)
