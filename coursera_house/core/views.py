from django.urls import reverse_lazy
from django.views.generic import FormView
from django.http import HttpResponse, HttpResponseRedirect
from .models import Setting
from .form import ControllerForm
import requests
import json
from django.forms import ValidationError
from coursera_house import settings


class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')
    headers = {
        'Authorization': 'Bearer {}'.format(settings.SMART_HOME_ACCESS_TOKEN),
    }
    resp = requests.get(settings.SMART_HOME_API_URL, headers=headers)
    resp = json.loads(resp.text)

    def get_context_data(self, **kwargs):
        context = super(ControllerView, self).get_context_data()
        #print(self.resp['data'])
        context['data'] = {i['name']: i['value'] for i in self.resp['data']}
        return context

    def get_initial(self):
        #print(self.request.POST)
        if self.resp['status'] != "ok":
            return HttpResponse(self.request, status=502)
        initial_dict = {i['name']: i['value'] for i in self.resp['data'] if i['name'] in ('bedroom_light',
                                                                                          'bathroom_light')}
        updater = Setting.objects.get(controller_name='bedroom_target_temperature')
        if not updater:
            initial_dict.update({'bedroom_target_temperature': 21})
        else:
            initial_dict.update({'bedroom_target_temperature': updater.value})
        updater = Setting.objects.get(controller_name='hot_water_target_temperature')
        if not updater:
            initial_dict.update({'hot_water_target_temperature': 80})
        else:
            initial_dict.update({'hot_water_target_temperature': updater.value})
        return initial_dict

    def form_valid(self, form):
        #print(self.request.POST)
        validation = ControllerForm(self.request.POST)
        if validation.is_valid():
            pass
        else:
            raise ValidationError
        params = Setting.objects.get(controller_name='bedroom_target_temperature')
        if not params:
            a = Setting(controller_name='bedroom_target_temperature',
                        label='bedroom',
                        value=self.request.POST['bedroom_target_temperature'])
            a.save()
        else:
            params.value = self.request.POST['bedroom_target_temperature']
            params.save()
        params = Setting.objects.get(controller_name='hot_water_target_temperature')
        if not params:
            a = Setting(controller_name='bedroom_target_temperature',
                        label='bedroom',
                        value=self.request.POST['hot_water_target_temperature'])
            a.save()
        else:
            params.value = self.request.POST['hot_water_target_temperature']
            params.save()
        return super(ControllerView, self).form_valid(form)
