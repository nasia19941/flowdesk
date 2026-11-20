def create_request(client, headers, workflow_id, submit=True) -> int:
    response = client.post(
        "/requests",
        headers=headers,
        json={"workflow_id": workflow_id, "title": "New laptop", "amount": "1200.00"},
    )
    request_id = response.json()["id"]
    if submit:
        client.post(f"/requests/{request_id}/submit", headers=headers)
    return request_id


def test_new_request_starts_as_draft(client, users, workflow):
    response = client.post(
        "/requests",
        headers=users["employee"],
        json={"workflow_id": workflow["id"], "title": "New laptop"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"


def test_submit_moves_request_to_first_step(client, users, workflow):
    request_id = create_request(client, users["employee"], workflow["id"], submit=False)

    response = client.post(f"/requests/{request_id}/submit", headers=users["employee"])

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["current_step_order"] == 1


def test_full_approval_flow(client, users, workflow):
    request_id = create_request(client, users["employee"], workflow["id"])

    for role, next_step in [("finance", 2), ("manager", 3)]:
        response = client.post(f"/requests/{request_id}/approve", headers=users[role], json={})
        assert response.status_code == 200
        assert response.json()["current_step_order"] == next_step

    response = client.post(
        f"/requests/{request_id}/approve", headers=users["admin"], json={"comment": "Go"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["current_step_order"] is None

    actions = client.get(f"/requests/{request_id}/actions", headers=users["employee"]).json()
    assert [action["step_order"] for action in actions] == [1, 2, 3]
    assert all(action["decision"] == "approved" for action in actions)


def test_wrong_role_cannot_approve(client, users, workflow):
    request_id = create_request(client, users["employee"], workflow["id"])

    response = client.post(f"/requests/{request_id}/approve", headers=users["manager"], json={})

    assert response.status_code == 403
    assert response.json()["detail"] == "This step needs a finance approver"


def test_requester_cannot_approve_own_request(client, users, workflow):
    request_id = create_request(client, users["manager"], workflow["id"])
    client.post(f"/requests/{request_id}/approve", headers=users["finance"], json={})

    response = client.post(f"/requests/{request_id}/approve", headers=users["manager"], json={})

    assert response.status_code == 403
    assert response.json()["detail"] == "You cannot decide on your own request"


def test_cannot_decide_on_draft(client, users, workflow):
    request_id = create_request(client, users["employee"], workflow["id"], submit=False)

    response = client.post(f"/requests/{request_id}/approve", headers=users["finance"], json={})

    assert response.status_code == 409


def test_reject_requires_comment(client, users, workflow):
    request_id = create_request(client, users["employee"], workflow["id"])

    response = client.post(f"/requests/{request_id}/reject", headers=users["finance"], json={})

    assert response.status_code == 422


def test_reject_ends_request(client, users, workflow):
    request_id = create_request(client, users["employee"], workflow["id"])

    response = client.post(
        f"/requests/{request_id}/reject",
        headers=users["finance"],
        json={"comment": "Over budget"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

    response = client.post(f"/requests/{request_id}/approve", headers=users["finance"], json={})
    assert response.status_code == 409


def test_pending_for_me_shows_only_current_step(client, users, workflow):
    request_id = create_request(client, users["employee"], workflow["id"])

    finance_ids = [r["id"] for r in client.get("/requests/pending-for-me", headers=users["finance"]).json()]
    manager_ids = [r["id"] for r in client.get("/requests/pending-for-me", headers=users["manager"]).json()]

    assert request_id in finance_ids
    assert request_id not in manager_ids


def test_other_employee_cannot_view_request(client, users, workflow, make_user):
    request_id = create_request(client, users["employee"], workflow["id"])
    stranger = make_user("stranger@test.dev")

    response = client.get(f"/requests/{request_id}", headers=stranger)

    assert response.status_code == 403