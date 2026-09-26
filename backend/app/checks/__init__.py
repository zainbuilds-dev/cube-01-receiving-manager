from . import carton_count, carton_damage, colour, quantity, sku, unit_damage, variant

CHECKS = {
    "sku_identity": sku.run,
    "colour": colour.run,
    "variant": variant.run,
    "quantity": quantity.run,
    "carton_count": carton_count.run,
    "carton_damage": carton_damage.run,
    "unit_damage": unit_damage.run,
}