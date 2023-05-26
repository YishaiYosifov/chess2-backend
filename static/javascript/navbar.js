const navbar = $($.parseHTML(
    `<nav class="navbar navbar-dark">
        <div class="container-fluid">
            <button class="navbar-toggler border-3 border-danger" type="button" data-bs-toggle="offcanvas" data-bs-target="#navbarOffcanvas" aria-controls="offcanvasDarkNavbar" aria-label="Toggle navigation">
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
                    <ul class="navbar-nav justify-content-end flex-grow-1 pe-3" id="body-top">
                    </ul>
                    <ul class="navbar-nav justify-content-end flex-grow-1 pe-3" id="body-bottom" style="display: none;">
                        <hr style="background-color: black;">
                    </ul>
                </div>
            </div>
        </div>
    </nav>`
));

function loadNavbar() {
    const root = location.protocol + "//" + location.host
    $.getJSON(`${root}/static/navbar.json`, async navbarItems => {
        const isLoggedIn = Object.keys(authInfo).length && authInfo["auth_method"] != "guest";

        const bodyTop = navbar.find(".offcanvas-body").find("#body-top");
        const bodyBottom = navbar.find(".offcanvas-body").find("#body-bottom");
        for (item of navbarItems) {
            if ((item["auth_req"] == 1 && !isLoggedIn) ||
                (item["auth_req"] == 2 && isLoggedIn)) continue;
    
            let navbarItem = $($.parseHTML("<li class='nav-item rounded'></li>"));
    
            let itemText = $("<a></a>");
            itemText.addClass("nav-link");
            if (item["path"] == window.location.pathname.split("/")[1]) itemText.addClass("active");
    
            itemText.attr("href", root + "/" + item["path"]);
            itemText.html(`<i class="bi ${item["icon"]}"></i> ㅤ ${item["label"]}`);
            navbarItem.append(itemText);
    
            if (item["side"] == "top") bodyTop.append(navbarItem);
            else if (item["side"] == "bottom") {
                if (bodyBottom.is(":hidden")) bodyBottom.show();
                
                bodyBottom.append(navbarItem);
            }
        };
        $("body").prepend(navbar);
    });
}
loadAuthInfo().then(loadNavbar);