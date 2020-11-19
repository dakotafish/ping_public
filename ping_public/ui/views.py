from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import generic

from sp.models import Entity
from .forms import NameForm



class Home(generic.ListView):
    attr = None
    #template_name = ''
    #context_object_name = 'Idk'

    def get(self, request, *args, **kwargs):
        return HttpResponse("Test Home Page.")

class EntityList(generic.ListView):
    #attr = None
    #template_name = ''
    #context_object_name = 'Idk'
    #model = Entity

    def get(self, request, *args, **kwargs):
        role = kwargs['role']
        return HttpResponse("Test Entity List. Role = " + role)


class EntityDetail(generic.DetailView):
    attr = None
    model = Entity
    #template_name = ''

    def get(self, request, *args, **kwargs):
        return HttpResponse("Test Entity Detail.")


def get_name(request):
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            #return HttpResponseRedirect('/thanks/')
            pass
    else:
        form = NameForm()

    return render(request, 'name.html', {'form': form})
