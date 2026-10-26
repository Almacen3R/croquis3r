import json
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from catalog.providers import get_catalog_provider
from catalog.pricing import quote, manual_rows, sketch_rows, template_rows
from .domain import validate_door_catalog, InvalidDocument, calculate, positive_int, validate_document
from .models import ObjectTemplate, Sketch, Attention
from .access import visible_to
from .attention import load_attention, saved_inputs, save_attention
from .house_calculator import HouseCalculatorForm, RECIPES, VERSION, calculate_house
from .modulation import calculate_modulation
from .panel_distribution import suggest_panels
from .house_templates import (HouseTemplateForm, TEMPLATES, TEMPLATES_BY_SLUG,
                              SOURCE_NAME, SOURCE_URL, VERSION as TEMPLATE_VERSION, template_result)


def authorized(request):
    return request.user.is_authenticated and request.user.is_active


def api(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not authorized(request):
            return JsonResponse({"error": "Inicie sesión con una cuenta del equipo.",
                "code": "authentication_required"}, status=403)
        try:
            return view(request, *args, **kwargs)
        except (InvalidDocument, json.JSONDecodeError, UnicodeDecodeError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)
    return wrapped


def payload(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise InvalidDocument("El cuerpo de la solicitud debe ser JSON válido.") from None
    if not isinstance(data, dict):
        raise InvalidDocument("Se esperaba un objeto JSON.")
    return data


def name(data, maximum=160):
    value = data.get("name")
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise InvalidDocument(f"Ingrese un nombre de 1 a {maximum} caracteres.")
    return value.strip()


def articles_by_id():
    return {a.id: a for a in get_catalog_provider().articles()}


@ensure_csrf_cookie
@require_GET
def editor(request):
    if not authorized(request):
        return redirect_to_login(request.get_full_path())
    assets = settings.BASE_DIR / "src/static/croquis"
    version = max((assets / name).stat().st_mtime_ns for name in ("editor.js", "editor.css", "geometry.mjs", "http.mjs"))
    return render(request, "sketches/editor.html", {"editor_asset_version": str(version),
        "csrf_cookie_name": settings.CSRF_COOKIE_NAME})


@require_http_methods(["GET", "POST"])
def house_calculator(request):
    if not authorized(request):
        return redirect_to_login(request.get_full_path())
    record = load_attention(request, "manual") if request.method == "GET" else None
    form = HouseCalculatorForm(request.POST if request.method == "POST" else saved_inputs(record) if record else None)
    result = calculate_house(form.cleaned_data) if form.is_bound and form.is_valid() else None
    if result is not None:
        result["pricing"] = quote(manual_rows(result))
    if result is not None and request.method == "POST" and request.POST.get("action") in ("save", "save_copy"):
        if not result["panels"]:
            form.add_error(None, "Agrega al menos un paño antes de guardar una atención de casa.")
            saved = None
        else:
            saved = save_attention(form, result, "manual", VERSION, user=request.user, copy=request.POST["action"] == "save_copy")
        if saved:
            return redirect("attention-detail", pk=saved.pk)
    groups = []
    for kind in dict.fromkeys(recipe.kind for recipe in RECIPES):
        groups.append({"name": kind, "rows": [
            {"recipe": recipe, "field": form[recipe.key]} for recipe in RECIPES if recipe.kind == kind]})
    return render(request, "sketches/house_calculator.html",
                  {"form": form, "groups": groups, "result": result, "version": VERSION,
                   "legacy_doors": form["panel_19"].value() not in (None, "", 0, "0"),
                   "record": record, "unsaved": request.method == "POST"},
                  status=400 if form.is_bound and form.errors else 200)


@require_GET
def house_templates(request):
    if not authorized(request):
        return redirect_to_login(request.get_full_path())
    return render(request, "sketches/house_templates.html", {
        "house_templates": TEMPLATES, "source_name": SOURCE_NAME, "source_url": SOURCE_URL})


@require_http_methods(["GET", "POST"])
def house_template_detail(request, slug):
    if not authorized(request):
        return redirect_to_login(request.get_full_path())
    template = TEMPLATES_BY_SLUG.get(slug)
    if template is None:
        raise Http404("Plantilla no encontrada.")
    record = load_attention(request, "template", slug) if request.method == "GET" else None
    form = HouseTemplateForm(template, request.POST if request.method == "POST" else saved_inputs(record) if record else None)
    if request.method == "GET" and record is None:
        original = {"project": f"Mi casa · {template.name}",
                    **{item.key: item.quantity for item in template.materials}}
        result = template_result(template, original)
    else:
        result = template_result(template, form.cleaned_data) if form.is_valid() else None
    if result is not None:
        result["pricing"] = quote(template_rows(result))
    if result is not None and request.method == "POST" and request.POST.get("action") in ("save", "save_copy"):
        saved = save_attention(form, result, "template", TEMPLATE_VERSION, slug, user=request.user,
                               copy=request.POST["action"] == "save_copy")
        if saved:
            return redirect("attention-detail", pk=saved.pk)
    rows = [{"name": item.name, "original": item.quantity, "field": form[item.key]}
            for item in template.materials]
    return render(request, "sketches/house_template_detail.html", {
        "house": template, "form": form, "rows": rows, "result": result,
        "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "version": TEMPLATE_VERSION,
        "record": record, "unsaved": request.method == "POST"},
        status=400 if form.is_bound and form.errors else 200)


@require_GET
def attentions(request):
    if not authorized(request):
        return redirect_to_login(request.get_full_path())
    query = request.GET.get("q", "").strip()[:160]
    records = visible_to(Attention, request.user)
    if query:
        records = records.filter(Q(project__icontains=query) | Q(customer__icontains=query))
    page = Paginator(records.defer("inputs", "notes"), 25).get_page(request.GET.get("page"))
    return render(request, "sketches/attentions.html", {"records": page, "query": query,
        "sketches": visible_to(Sketch, request.user).order_by("-updated_at").values("id", "name", "is_template")[:20]})


@require_GET
def attention_detail(request, pk):
    if not authorized(request):
        return redirect_to_login(request.get_full_path())
    record = get_object_or_404(visible_to(Attention, request.user), pk=pk)
    if record.kind == "manual":
        rows = [{"name": label, "quantity": quantity, "unit": unit} for label, quantity, unit in record.result["items"]]
        edit_url = reverse("house-calculator")
    else:
        rows = [{**row, "unit": "unidades"} for row in record.result["rows"]]
        edit_url = reverse("house-template-detail", args=[record.template_slug])
    return render(request, "sketches/attention_detail.html", {"record": record, "rows": rows,
        "edit_url": f"{edit_url}?attention={pk}", "unknown": any(row["quantity"] is None for row in rows)})


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok", "application": "croquis3r"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


@require_GET
@api
def catalog(request):
    return JsonResponse({"articles": [{"id": a.id, "sku": a.sku, "name": a.name,
        "unit": a.unit, "is_demo": a.is_demo} for a in get_catalog_provider().articles()]})


@require_http_methods(["POST"])
@api
def estimate(request):
    return JsonResponse(calculate(payload(request).get("document"), articles_by_id()))


@require_http_methods(["POST"])
@api
def ticoblock_estimate(request):
    result = calculate_modulation(payload(request).get("document"), articles_by_id())
    if result["status"] == "ready":
        result["pricing"] = quote(sketch_rows(result))
    return JsonResponse(result)


@require_http_methods(["POST"])
@api
def panel_suggestion(request):
    data = payload(request)
    return JsonResponse(suggest_panels(data.get("meters"), data.get("preferred", "2")))


@require_http_methods(["GET", "POST"])
@api
def sketches(request):
    if request.method == "GET":
        return JsonResponse({"sketches": list(visible_to(Sketch, request.user).values("id", "name", "is_template", "revision", "updated_at"))})
    data = payload(request)
    if type(data.get("is_template", False)) is not bool:
        raise InvalidDocument("El indicador de plantilla debe ser booleano.")
    sketch = Sketch.objects.create(owner=request.user, name=name(data), is_template=data.get("is_template", False),
        document=validate_door_catalog(validate_document(data.get("document"), articles_by_id())))
    return JsonResponse(serialize(sketch), status=201)


def serialize(sketch):
    return {"id": sketch.id, "name": sketch.name, "document": sketch.document,
            "is_template": sketch.is_template, "revision": sketch.revision}


@require_http_methods(["GET", "PUT"])
@api
def sketch_detail(request, pk):
    sketch = visible_to(Sketch, request.user).filter(pk=pk).first()
    if not sketch:
        return JsonResponse({"error": "Croquis no encontrado."}, status=404)
    if request.method == "GET":
        return JsonResponse(serialize(sketch))
    data = payload(request)
    revision = positive_int(data.get("revision"), "Revisión")
    document = validate_door_catalog(validate_document(data.get("document"), articles_by_id()))
    updated = visible_to(Sketch, request.user).filter(pk=pk, revision=revision).update(
        name=name(data), document=document, revision=revision + 1, updated_at=timezone.now())
    if not updated:
        return JsonResponse({"error": "Otra sesión modificó este croquis. Guarde una copia o vuelva a abrirlo."}, status=409)
    sketch.refresh_from_db()
    return JsonResponse(serialize(sketch))


@require_http_methods(["GET", "POST"])
@api
def object_templates(request):
    if request.method == "GET":
        return JsonResponse({"templates": list(visible_to(ObjectTemplate, request.user).order_by("name").values("id", "name", "specification"))})
    data = payload(request)
    document = validate_document({"version": 1, "objects": [data.get("specification")]}, articles_by_id())
    specification = document["objects"][0]
    if specification["kind"] != "wall":
        raise InvalidDocument("En esta primera versión las plantillas de objeto son de paredes.")
    obj = ObjectTemplate.objects.create(owner=request.user, name=name(data, 100), specification=specification)
    return JsonResponse({"id": obj.id, "name": obj.name, "specification": obj.specification}, status=201)
