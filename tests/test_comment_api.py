

async def test_get_comment(cli, app_db):
    response = await cli.get('/comment/10002')
    assert response.status == 200
    assert 'Test comment' in await response.text()

    response = await cli.get('/comment/')
    assert response.status == 200
    assert 'error' in await response.text()


async def test_update_comment(cli, app_db):
    text = "New text"
    data = {'text': text, 'user_id': 1}
    response = await cli.put('/comment/10002', data=data)
    assert response.status == 200
    assert text in await response.text()


async def test_insert_comment(cli, app_db):
    data = {
        'text': "Insert Text",
        'user_id': 1,
        'entity_type': 'product',
        'entity_id': 1
        }
    response = await cli.post('/comment/', data=data)
    assert response.status == 200
    assert data['text'] in await response.text()


async def test_delete_comment(cli, app_db):
    response = await cli.delete('/comment/10002', data={'user_id': 1})
    assert response.status == 200
    assert 'success' in await response.text()
