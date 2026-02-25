from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.classification.classifier import OpportunityClassifier
from apps.opportunities.models import Opportunity


@login_required
@require_POST
def classify_opportunity(request, pk):
    classifier = OpportunityClassifier()
    domain = classifier.classify_opportunity(pk)
    if not domain:
        return JsonResponse({"status": "error"}, status=400)
    return JsonResponse({"status": "ok", "domain": domain})


@login_required
def classify_pending(request):
    classifier = OpportunityClassifier()
    pending_ids = list(
        Opportunity.objects.filter(domain__isnull=True, is_active=True).values_list("id", flat=True)[:100]
    )
    updated = 0
    for opportunity_id in pending_ids:
        if classifier.classify_opportunity(opportunity_id):
            updated += 1
    return JsonResponse({"status": "ok", "updated": updated, "total": len(pending_ids)})
