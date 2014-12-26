from uuid import uuid4

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404

from .forms import EventForm, EventAttendyForm, CommentForm
from .models import Event, EventAttending, Comment


def new_event(request):
    form = EventForm(request.POST) if request.method == "POST" else EventForm()

    if request.method == "POST" and form.is_valid():
        event = Event()
        event.title = form.cleaned_data["title"]
        event.slug = form.generate_slug()

        event.description = form.cleaned_data["description"]

        event.admin_id = form.generate_admin_id()

        event.date = form.cleaned_data["date"]
        event.time = form.cleaned_data["time"]

        event.location_address = form.cleaned_data["location_address"]

        event.save()

        return HttpResponseRedirect(reverse("event_admin", args=(event.admin_id,)))

    return render(request, "events/new.haml", {
        "form": form,
        "current_base_url": request.META["wsgi.url_scheme"] + "://" + request.META["SERVER_NAME"] + "/",
    })


def event_admin(request, admin_id):
    def remove_first_zero(time):
        if time.startswith("0"):
            return time[1:]
        return time

    event = get_object_or_404(Event, admin_id=admin_id)

    if request.method == "POST":
        form = EventForm(request.POST)
    else:
        form = EventForm({
            "title": event.title,
            "description": event.description,
            "date": event.date.strftime("%d/%m/%Y") if event.date else None,
            "time": remove_first_zero(event.time.strftime("%H:%M")) if event.time else None,
            "location_address": event.location_address,
        })

    if request.method == "POST" and form.is_valid():
        event.title = form.cleaned_data["title"]

        event.description = form.cleaned_data["description"]

        event.date = form.cleaned_data["date"]
        event.time = form.cleaned_data["time"]

        event.location_address = form.cleaned_data["location_address"]

        event.save()

        return HttpResponseRedirect(reverse("event_admin", args=(event.admin_id,)))

    return render(request, "events/event_form.haml", {
        "form": form,
        "event": event,
        "current_base_url": request.META["wsgi.url_scheme"] + "://" + request.META["SERVER_NAME"] + "/",
        "current_page_url": request.META["wsgi.url_scheme"] + "://" + request.META["SERVER_NAME"] + request.META["PATH_INFO"],
    })


def event_view(request, slug, user_uuid=None):
    event = get_object_or_404(Event, slug=slug)

    event_attending = get_object_or_404(EventAttending, uuid=user_uuid) if user_uuid else None

    in_comment_posting_mode = request.method == "POST" and "comment_name" in request.POST and "comment_content" in request.POST

    comment_form = CommentForm(request.POST) if in_comment_posting_mode else CommentForm()

    if request.method == "POST" and not in_comment_posting_mode:
        form = EventAttendyForm(request.POST)
    elif event_attending:
        form = EventAttendyForm({
            "name": event_attending.name,
            "choice": event_attending.choice,
        })
    else:
        form = EventAttendyForm()

    if in_comment_posting_mode and comment_form.is_valid():
        Comment.objects.create(
            name=comment_form.cleaned_data["comment_name"],
            content=comment_form.cleaned_data["comment_content"],
            event=event,
        )

        if event_attending:
            return HttpResponseRedirect(reverse("event_detail_uuid", args=(event.slug, event_attending.uuid)))
        else:
            return HttpResponseRedirect(reverse("event_detail_uuid", args=(event.slug,)))

    if not in_comment_posting_mode and request.method == "POST" and form.is_valid():
        if event_attending:
            event_attending.name = form.cleaned_data["name"]
            event_attending.choice = form.cleaned_data["choice"]
            event_attending.save()
        else:
            event_attending = EventAttending.objects.create(
                name=form.cleaned_data["name"],
                choice=form.cleaned_data["choice"],
                event=event,
                uuid=str(uuid4()),
            )

        return HttpResponseRedirect(reverse("event_detail_uuid", args=(event.slug, event_attending.uuid)))

    return render(request, "events/event_detail.haml", {
        "event": event,
        "form": form,
        "comment_form": comment_form,
        "event_attending": event_attending,
        "current_page_url": request.META["wsgi.url_scheme"] + "://" + request.META["SERVER_NAME"] + request.META["PATH_INFO"],
    })
