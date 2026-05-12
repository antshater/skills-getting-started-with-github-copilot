import pytest
from httpx import AsyncClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    @pytest.mark.asyncio
    async def test_get_activities_returns_all_activities(self, client: AsyncClient):
        """Test that GET /activities returns all activities with correct structure"""
        # Arrange
        expected_activity_names = [
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Club",
            "Science Club",
            "Chess Club",
            "Programming Class",
            "Gym Class",
        ]

        # Act
        response = await client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert set(activities.keys()) == set(expected_activity_names)

    @pytest.mark.asyncio
    async def test_get_activities_returns_correct_structure(self, client: AsyncClient):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = await client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    @pytest.mark.asyncio
    async def test_get_activities_chess_club_has_participants(self, client: AsyncClient):
        """Test that pre-populated participants are returned"""
        # Arrange
        # Act
        response = await client.get("/activities")
        activities = response.json()

        # Assert
        chess_club = activities["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    @pytest.mark.asyncio
    async def test_root_redirects_to_static_index(self, client: AsyncClient):
        """Test that GET / redirects to /static/index.html"""
        # Arrange
        # Act
        response = await client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    @pytest.mark.asyncio
    async def test_signup_successful_adds_participant(self, client: AsyncClient):
        """Test successful signup adds email to participants list"""
        # Arrange
        activity_name = "Basketball Team"
        email = "student@mergington.edu"

        # Act
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]

        # Verify participant was added
        activities_response = await client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    @pytest.mark.asyncio
    async def test_signup_nonexistent_activity_returns_404(self, client: AsyncClient):
        """Test signup for non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert result["detail"] == "Activity not found"

    @pytest.mark.asyncio
    async def test_signup_duplicate_email_returns_400(self, client: AsyncClient):
        """Test signing up with same email twice returns 400"""
        # Arrange
        activity_name = "Basketball Team"
        email = "student@mergington.edu"

        # First signup
        await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Act - Try to sign up again with same email
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert result["detail"] == "Student already signed up"

    @pytest.mark.asyncio
    async def test_signup_missing_email_parameter(self, client: AsyncClient):
        """Test signup without email parameter"""
        # Arrange
        activity_name = "Basketball Team"

        # Act
        response = await client.post(f"/activities/{activity_name}/signup")

        # Assert
        assert response.status_code == 422  # Unprocessable Entity - missing required param

    @pytest.mark.asyncio
    async def test_signup_multiple_participants(self, client: AsyncClient):
        """Test that multiple different emails can sign up for same activity"""
        # Arrange
        activity_name = "Soccer Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]

        # Act
        for email in emails:
            response = await client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email},
            )
            assert response.status_code == 200

        # Assert
        activities_response = await client.get("/activities")
        activities = activities_response.json()
        participants = activities[activity_name]["participants"]

        for email in emails:
            assert email in participants
        assert len(participants) == 3


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    @pytest.mark.asyncio
    async def test_unregister_removes_participant(self, client: AsyncClient):
        """Test successful unregistration removes email from participants list"""
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"

        # Verify participant exists before unregister
        activities_response = await client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

        # Act
        response = await client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]

        # Verify participant was removed
        activities_response = await client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_activity_returns_404(self, client: AsyncClient):
        """Test unregister from non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = await client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert result["detail"] == "Activity not found"

    @pytest.mark.asyncio
    async def test_unregister_email_not_in_activity_returns_400(self, client: AsyncClient):
        """Test unregister for email not in activity returns 400"""
        # Arrange
        activity_name = "Art Club"
        email = "notregistered@mergington.edu"

        # Act
        response = await client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert result["detail"] == "Student not signed up"

    @pytest.mark.asyncio
    async def test_unregister_missing_email_parameter(self, client: AsyncClient):
        """Test unregister without email parameter"""
        # Arrange
        activity_name = "Basketball Team"

        # Act
        response = await client.delete(f"/activities/{activity_name}/signup")

        # Assert
        assert response.status_code == 422  # Unprocessable Entity - missing required param

    @pytest.mark.asyncio
    async def test_unregister_then_signup_again(self, client: AsyncClient):
        """Test that unregistered participant can sign up again"""
        # Arrange
        activity_name = "Drama Club"
        email = "student@mergington.edu"

        # Sign up
        response1 = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        assert response1.status_code == 200

        # Unregister
        response2 = await client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        assert response2.status_code == 200

        # Act - Sign up again
        response3 = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response3.status_code == 200
        activities_response = await client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
