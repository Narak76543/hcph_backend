
from core.app import app

def register_routes() -> None:
    import api.users.views  # noqa: F401
    import api.shops.views  # noqa: F401
    import api.role_request.views  # noqa: F401
    import api.shop_listing.views  # noqa: F401
    import api.part_category.views  # noqa: F401
    import api.part.views  # noqa: F401
    from api.shop_listing.views import register_shop_listing_routes
    from api.compatibility_rule.views import register_compatibility_routes
    from api.laptop_brands.views import register_laptop_brand_routes
    from api.laptop_models.views import register_laptop_model_routes
    from api.laptop_specs.views import register_laptop_spec_routes
    from api.user_laptops.views import register_user_laptop_routes

    register_shop_listing_routes(app)
    register_compatibility_routes(app)
    register_laptop_brand_routes(app)
    register_laptop_model_routes(app)
    register_laptop_spec_routes(app)
    register_user_laptop_routes(app)