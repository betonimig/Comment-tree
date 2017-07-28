import aiohttp
import asyncio

# Тестируем уведомления об изменениях комментариев по websocket
async def main():
    session = aiohttp.ClientSession()

    while True:
        try:
            async with session.ws_connect('http://localhost:8000/comment/ws/product/1/') as ws:
                async for msg in ws:
                    print(msg.type)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        print('Message:{}'.format(msg.data))
                        if msg.data == 'close cmd':
                            await ws.close()
                            break
                        else:
                            await ws.send_str(msg.data + '/answer')
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
        except Exception as e:
            print(e)
        await asyncio.sleep(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
