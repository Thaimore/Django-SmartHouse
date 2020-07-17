from __future__ import absolute_import, unicode_literals
from celery import task
import requests
from .models import Setting
import json
from django.core.mail import send_mail
from coursera_house import settings


@task()
def smart_home_manager():
    bedroom = Setting.objects.get(controller_name='bedroom_target_temperature')
    water_temp = Setting.objects.get(controller_name='hot_water_target_temperature')
    headers = {
        'Authorization': 'Bearer {}'.format(settings.SMART_HOME_ACCESS_TOKEN),
    }
    resp = json.loads(
        requests.get('{}'.format(settings.SMART_HOME_API_URL), headers=headers).text
    )
    data = {"controllers": []}
    work_dict = {i['name']: i['value'] for i in resp['data']}

    if work_dict['leak_detector']:
        if work_dict['cold_water']:
            data["controllers"] += [{'name': 'cold_water', 'value': False}]
            work_dict['cold_water'] = False
        if work_dict['hot_water']:
            data["controllers"] += [{'name': 'hot_water', 'value': False}]
            work_dict['hot_water'] = False
        send_mail(
            'Subject here',
            'Here is the message.',
            '{}'.format(settings.EMAIL_HOST),
            ['{}'.format(settings.EMAIL_RECEPIENT)],
            fail_silently=True,
        )
    if not work_dict['cold_water'] or work_dict['smoke_detector']:
        if work_dict['smoke_detector']:
            if work_dict['air_conditioner']:
                data["controllers"] += [{'name': 'air_conditioner', 'value': False}]
                work_dict['air_conditioner'] = False
            if work_dict['bedroom_light']:
                data["controllers"] += [{'name': 'bedroom_light', 'value': False}]
                work_dict['bedroom_light'] = False
            if work_dict['bathroom_light']:
                data["controllers"] += [{'name': 'bathroom_light', 'value': False}]
                work_dict['bathroom_light'] = False
        if work_dict['washing_machine'] != 'off':
            data["controllers"] += [{'name': 'washing_machine', 'value': 'off'}]
            work_dict['washing_machine'] = 'off'
        if work_dict['boiler']:
            data["controllers"] += [{'name': 'boiler', 'value': False}]
            work_dict['boiler'] = False
    else:
        if work_dict['boiler_temperature'] < (water_temp.value - (water_temp.value // 10)) and not work_dict['boiler']:
            data["controllers"] += [{'name': 'boiler', 'value': True}]
            work_dict['boiler'] = True
        if work_dict['boiler_temperature'] > (water_temp.value + (water_temp.value // 10)) and work_dict['boiler']:
            data["controllers"] += [{'name': 'boiler', 'value': False}]
            work_dict['boiler'] = False

    if work_dict['curtains'] != 'slightly_open':
        if work_dict['outdoor_light'] < 50 and work_dict['curtains'] != 'open' and not work_dict['bedroom_light']:
            data["controllers"] += [{'name': 'curtains', 'value': 'open'}]
            work_dict['curtains'] = 'open'
        if (work_dict['outdoor_light'] > 50 or work_dict['bedroom_light']) and work_dict['curtains'] != 'close':
            data["controllers"] += [{'name': 'curtains', 'value': 'close'}]
            work_dict['curtains'] = 'close'

    if not work_dict['smoke_detector']:
        if work_dict['bedroom_temperature'] > (bedroom.value + (bedroom.value // 10)) and not work_dict['air_conditioner']:
            data["controllers"] += [{'name': 'air_conditioner', 'value': True}]
            work_dict['air_conditioner'] = True
        if work_dict['bedroom_temperature'] < (bedroom.value - (bedroom.value // 10)) and work_dict['air_conditioner']:
            data["controllers"] += [{'name': 'air_conditioner', 'value': False}]
            work_dict['air_conditioner'] = False

    if data["controllers"]:
        requests.post('{}'.format(settings.SMART_HOME_API_URL), headers=headers, data=json.dumps(data))
