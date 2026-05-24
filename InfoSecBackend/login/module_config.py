AVAILABLE_MODULES = [
    "Home",
    "View Documents",
    "Recent News",
    "Create Edit Documents",
    "Edit Home/News",
    # Insert New Module/s Here
    "User Management",
]

DEFAULT_ROLE_MODULES = {
    "Admin": AVAILABLE_MODULES.copy(),
    "Staff": AVAILABLE_MODULES[:-1],
}