from . import damage, quantity, sku, variant

CHECKS = {
    "sku_identity": sku.run,
    "quantity": quantity.run,
    "variant": variant.run,
    "carton_damage": damage.run,
}