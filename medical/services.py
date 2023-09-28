from gettext import gettext as _
from core.signals import register_service_signal


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


def reset_item_before_update(item):
    item.code = None
    item.name = None
    item.type = None
    item.price = None
    item.care_type = None
    item.patient_category = None
    item.package = None
    item.quantity = None
    item.frequency = None


def reset_service_before_update(service):
    service.code = None
    service.category = None
    service.type = None
    service.name = None
    service.level = None
    service.patient_category = None
    service.price = None
    service.frequency = None
    service.maximum_amount = None
    service.care_type = None


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


class MedicationItemService:
    def __init__(self, user):
        self.user = user

    @register_service_signal('medication_item.create_or_update')
    def create_or_update(self, data):

        from .models import Item

        data['audit_user_id'] = self.user.id_for_audit

        medicationItem_uuid = data.pop('uuid', None)

        if Item.objects.filter(uuid=medicationItem_uuid).count() == 0:
            item = Item.objects.create(**data)
            return item

        item = Item.objects.get(uuid=medicationItem_uuid)

        # Handle Update of medication item
        item.save_history()
        # reset the non required fields
        # (each update is 'complete', necessary to be able to set 'null')
        reset_item_before_update(item)

        [setattr(item, key, data[key]) for key in data]

        item.save()

        return item


class MedicationServiceService:
    def __init__(self, user):
        self.user = user

    @register_service_signal('medication_service.create_or_update')
    def create_or_update(self, data):

        from .models import Service

        data['audit_user_id'] = self.user.id_for_audit

        medicationService_uuid = data.pop('uuid', None)

        if Service.objects.filter(uuid=medicationService_uuid).count() == 0:

            service = Service.objects.create(**data)

            return service

        service = Service.objects.get(uuid=medicationService_uuid)

        # Handle Update of medication item
        service.save_history()
        # reset the non requssired fields
        # (each update is 'complete', necessary to be able to set 'null')
        reset_service_before_update(service)

        [setattr(service, key, data[key]) for key in data]

        service.save()

        return service
