# -*- coding: utf-8 -*-
import asyncio
from PIL import Image
from io import BytesIO
from os.path import dirname, abspath, join as pjoin
from os import remove
from random import randint as rnt
from numpy import array, expand_dims, float32, uint8
from onnxruntime import InferenceSession
import aiohttp

CDIR = dirname(abspath(__file__))

async def solve(image=None, sid=None, s=None):
    if sid is None:
        img = Image.open(image).resize((128, 64)).convert('RGB')
    else:
        fname = 'cap{}tcha.png'.format(rnt(-99999999999, 99999999999))
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            if s is not None:
                url = 'https://api.vk.com/captcha.php?sid={}&s={}'.format(sid, s)
            else:
                url = 'https://api.vk.com/captcha.php?sid={}'.format(sid)
            async with session.get(url) as resp:
                content = await resp.read()
                with open(pjoin(CDIR, fname), 'wb') as f:
                    f.write(content)
        img = Image.open(pjoin(CDIR, fname)).resize((128, 64)).convert('RGB')

    x = array(img).reshape(1, -1)
    x = expand_dims(x, axis=0)
    x = x / float32(255.)

    session = InferenceSession(pjoin(CDIR, 'captcha_model.onnx'))
    session2 = InferenceSession(pjoin(CDIR, 'ctc_model.onnx'))

    out = session.run(None, dict([(inp.name, x[n]) for n, inp in enumerate(session.get_inputs())]))
    out = session2.run(None, dict([(inp.name, float32(out[n])) for n, inp in enumerate(session2.get_inputs())]))

    codemap = ' 24578acdehkmnpqsuvxyz'

    captcha = ''.join([codemap[c] for c in uint8(out[-1][out[0] > 0])])
    if image is None:
        remove(pjoin(CDIR, fname))
    return captcha