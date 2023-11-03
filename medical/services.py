import django.db.models.base
from medical.exceptions import CodeAlreadyExistsError
from gettext import gettext as _
from core.signals import register_service_signal
# from medical.gql_mutations import check_if_code_already_exists, reset_item_or_service_before_update


def set_item_or_service_deleted(item_service, item_or_service_element):
    """
    Marks an Item or Service as deleted, cascading onto the pricelists
    :param item_service: the object to mark as deleted
    :param item_or_service_element: either "item" or "service", used for translation keys
    :return: an empty array is everything goes well, an array with errors if any
    """
    try:
        item_service.delete_history()
        [pld.delete_history() for pld in item_service.pricelist_details.filter(validity_to__isnull=True)]
        return []
    except Exception as exc:
        return {
            'title': item_service.uuid,
            'list': [{
                'message': _(f"medical.mutation.failed_to_delete_{item_or_service_element}")
                % {'uuid': item_service.uuid},
                'detail': item_service.uuid}]
        }


def clear_item_dict(item):
    new_dict = {
        "code": item.code,
        "name": item.name,
        "type": item.type,
        "price": item.price,
        "care_type": item.care_type,
        "patient_category": item.patient_category,
        "package": item.package,
        "quantity": item.quantity,
        "frequency": item.frequency,
    }
    return new_dict


def reset_item_or_service_before_update(item_service):
    fields = [
        "code",
        "name",
        "code",
        "name",
        "type",
        "price",
        "frequency",
        "care_type",
        "patient_category",
        "category",
        "level",    # service only
        "category", # service only
        "package",  # item only
        "quantity", # item only
    ]
    for field in fields:
        if hasattr(item_service, field):
            setattr(item_service, field, None)


def check_if_code_already_exists(
        data: dict,
        item_service_model: django.db.models.base.ModelBase
):
    if item_service_model.objects.all().filter(code=data['code'], validity_to__isnull=True).exists():
        raise CodeAlreadyExistsError(_("Code already exists."))
# def reset_item_before_update(item):
#     item.code = None
#     item.name = None
#     item.type = None
#     item.price = None
#     item.care_type = None
#     item.patient_category = None
#     item.package = None
#     item.quantity = None
#     item.frequency = None


# def reset_service_before_update(service):
#     service.code = None
#     service.category = None
#     service.type = None
#     service.name = None
#     service.level = None
#     service.patient_category = None
#     service.price = None
#     service.frequency = None
#     service.maximum_amount = None
#     service.care_type = None


def check_unique_code_service(code):
    from .models import Service
    if Service.objects.filter(code=code, validity_to__isnull=True).exists():
        return [{"message": "Services code %s already exists" % code}]
    return []


def check_unique_code_item(code):
    from .models import Item
    if Item.objects.filter(code=code, validity_to__isnull=True).exists():
        return [{"message": "Items code %s already exists" % code}]
    return []


def create_item_or_service(data, item_service_model):
    item_service_uuid = data.pop('uuid') if 'uuid' in data else None
    # update_or_create(uuid=service_uuid, ...)
    # doesn't work because of explicit attempt to set null to uuid!
    
    # data["audit_user_id"] = user.id_for_audit
    data["audit_user_id"] = 1
    
    incoming_code = data.get('code')
    item_service = item_service_model.objects.filter(uuid=item_service_uuid).first()
    current_code = item_service.code if item_service else None
        
    if current_code != incoming_code:
        check_if_code_already_exists(data, item_service_model)
         
    if item_service_uuid:
        reset_item_or_service_before_update(item_service)
        [setattr(item_service, key, data[key]) for key in data]
    else:
        item_service = item_service_model.objects.create(**data)

    item_service.save()
    
    return item_service


class MedicationItemService:
    def __init__(self, user):
        self.user = user

    @register_service_signal('medication_item.create_or_update')
    def create_or_update(self, data, model):
        return create_item_or_service(data, model)

class MedicationServiceService:
    def __init__(self, user):
        self.user = user

    @register_service_signal('medication_service.create_or_update')
    def create_or_update(self, data, model):

        return create_item_or_service(data, model)
