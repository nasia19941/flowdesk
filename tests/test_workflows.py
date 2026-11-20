def test_admin_can_create_workflow(workflow):
    assert workflow["name"] == "Expense"
    assert [step["step_order"] for step in workflow["steps"]] == [1, 2, 3]


def test_manager_cannot_create_workflow(client, users):
    response = client.post(
        "/workflows",
        headers=users["manager"],
        json={"name": "Leave", "steps": [{"name": "Approve", "approver_role": "manager"}]},
    )

    assert response.status_code == 403


def test_employee_cannot_be_approver(client, users):
    response = client.post(
        "/workflows",
        headers=users["admin"],
        json={"name": "Leave", "steps": [{"name": "Approve", "approver_role": "employee"}]},
    )

    assert response.status_code == 422


def test_duplicate_workflow_name_returns_409(client, users, workflow):
    response = client.post(
        "/workflows",
        headers=users["admin"],
        json={"name": "Expense", "steps": [{"name": "Approve", "approver_role": "admin"}]},
    )

    assert response.status_code == 409


def test_cannot_delete_workflow_with_requests(client, users, workflow):
    client.post(
        "/requests",
        headers=users["employee"],
        json={"workflow_id": workflow["id"], "title": "New laptop"},
    )

    response = client.delete(f"/workflows/{workflow['id']}", headers=users["admin"])

    assert response.status_code == 409