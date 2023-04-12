const navbar = $($.parseHTML(
    `<nav class="navbar navbar-dark">
        <div class="container-fluid">
            <button class="navbar-toggler" type="button" data-bs-toggle="offcanvas" data-bs-target="#navbarOffcanvas" aria-controls="offcanvasDarkNavbar" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="offcanvas offcanvas-start" tabindex="-1" id="navbarOffcanvas" aria-labelledby="navbarOffcanvas" style="background-color: #687c8b;">
                <div class="offcanvas-header">
                    <a href="/" class="nav-link offcanvas-title">
                        <h5>
                            <img src="/static/assets/logo.png" alt="Logo" width="30" height="30" class="d-inline-block align-text-top rounded">
                            <b>Chess 2</b>
                        </h5>
                    </a>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Close"></button>
                </div>
                <div class="offcanvas-body">
                    <ul class="navbar-nav justify-content-end flex-grow-1 pe-3">
                    </ul>
                </div>
            </div>
        </div>
    </nav>`
));

var root = location.protocol + "//" + location.host
$.getJSON(`${root}/static/navbar.json`, navbarItems => {
    const navbarBody = navbar.find(".offcanvas-body").find("ul");
    for (item of navbarItems) {
        var navbarItem = $($.parseHTML("<li class='nav-item rounded'></li>"));

        var itemText = $("<a></a>");
        itemText.addClass("nav-link");
        if (item["path"] == window.location.pathname.split("/")[1]) itemText.addClass("active");

        itemText.attr("href", root + "/" + item["path"]);
        itemText.html(`<i class="bi ${item["icon"]}"></i> ${item["label"]}`);
        navbarItem.append(itemText);

        navbarBody.append(navbarItem);
    };
    $("body").prepend(navbar);
});