import io
import uuid
from fastapi.testclient import TestClient

# 1. Imports from your app
from main import app
from core.db import get_db
from core.security import require_admin
from sqlalchemy.orm import Session

# Generate random identifier to avoid unique constraint errors
RANDOM_SUFFIX = str(uuid.uuid4())[:8]
TEST_CATEGORY_SLUG = None

# Dependency Overrides
class MockAdmin:
    id = str(uuid.uuid4())
    role = "ADMIN"

def override_require_admin():
    return MockAdmin()

# Mock the database session for POST and PATCH to prevent actual writes, 
# or just allow writing to the user's PostgreSQL database if it exists!
# Here we just override the admin requirement so we can test the routes.
app.dependency_overrides[require_admin] = override_require_admin

client = TestClient(app)

def test_create_category():
    global TEST_CATEGORY_SLUG

    payload = {
        "name": f"Test Category {RANDOM_SUFFIX}", 
        "slug": f"test-category-{RANDOM_SUFFIX}"
    }
    TEST_CATEGORY_SLUG = payload["slug"]

    # Create a mock image file
    file_content = b"fake image content"
    files = {"category_image": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    response = client.post("/part-categories/", data=payload, files=files)
    assert response.status_code == 201, f"Failed create: {response.text}"
    data = response.json()
    assert data["name"] == payload["name"]
    assert "part_category_img_url" in data
    assert data["part_category_img_url"] is not None
    assert "id" in data
    return data["id"]

def test_get_all_categories():
    response = client.get("/part-categories/")
    assert response.status_code == 200, f"Failed get all: {response.text}"
    assert isinstance(response.json(), list)

def test_get_one_category(cat_id):
    response = client.get(f"/part-categories/{cat_id}")
    assert response.status_code == 200, f"Failed get one: {response.text}"
    assert response.json()["id"] == cat_id


def test_get_category_by_slug():
    assert TEST_CATEGORY_SLUG is not None, "TEST_CATEGORY_SLUG must be set by test_create_category"
    response = client.get(f"/part-categories/slug/{TEST_CATEGORY_SLUG}")
    assert response.status_code == 200, f"Failed get by slug: {response.text}"
    assert response.json()["slug"] == TEST_CATEGORY_SLUG


def test_update_category(cat_id):
    update_payload = {
        "name": f"Updated Category {RANDOM_SUFFIX}",
    }
    file_content = b"fake updated image content"
    files = {"category_image": ("updated.jpg", io.BytesIO(file_content), "image/jpeg")}
    
    response = client.patch(f"/part-categories/{cat_id}", data=update_payload, files=files)
    assert response.status_code == 200, f"Failed update: {response.text}"
    assert response.json()["name"] == update_payload["name"]
    assert "part_category_img_url" in response.json()

def test_delete_category(cat_id):
    response = client.delete(f"/part-categories/{cat_id}")
    assert response.status_code == 204, f"Failed delete: {response.text}"
    
    # Confirm deletion
    response = client.get(f"/part-categories/{cat_id}")
    assert response.status_code == 404

if __name__ == "__main__":
    print("\nRunning Part Category tests...")
    try:
        new_id = test_create_category()
        print("✅ test_create_category passed")
        
        test_get_all_categories()
        print("✅ test_get_all_categories passed")
        
        if new_id:
            test_get_one_category(new_id)
            print("✅ test_get_one_category passed")

            test_get_category_by_slug()
            print("✅ test_get_category_by_slug passed")
            
            test_update_category(new_id)
            print("✅ test_update_category passed")
            
            test_delete_category(new_id)
            print("✅ test_delete_category passed")
            
        print("\n🎉 All API checks passed perfectly!")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        print("Make sure your PostgreSQL database is running and accessible (via localhost:5432 or as setup in your .env file).")
