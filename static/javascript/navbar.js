const navbar = $($.parseHTML(`
    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <button class="navbar-toggler shadow-none text-white border-0 align-items-center d-flex d-lg-none" type="button" data-bs-toggle="offcanvas" data-bs-target="#navbarOffcanvas" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle offcanvas">
                <i class="bi bi-list" style="font-size: 50px;"></i>
                <a class="navbar-brand text-white">Chess 2</a>
            </button>
            <div class="collapse navbar-collapse navbar-top">
                <ul class="navbar-nav">
                    <a class="navbar-brand" style="color: #99999a;" href="/">Chess 2</a>

                    <li class="nav-item" id="navbar-seperator">
                        <a class="nav-link">|</a>
                    </li>
                </ul>
            </div>
        </div>
        <div class="offcanvas offcanvas-start d-flex d-lg-none" tabindex="-1" id="navbarOffcanvas" aria-labelledby="navbarOffcanvas" style="background-color: #687c8b;">
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
                <ul class="navbar-nav justify-content-end flex-grow-1 pe-3" id="offset-top">
                </ul>
                <ul class="navbar-nav justify-content-end flex-grow-1 pe-3" id="offset-bottom">
                    <hr style="background-color: black;">
                </ul>
            </div>
        </div>
    </nav>`
));

const navItem = $($.parseHTML(`
    <li class="nav-item">
        <a class="nav-link">
            <i class="bi"></i>
        </a>
    </li>
`))

function loadNavbar() {
    const root = location.protocol + "//" + location.host
    $.getJSON(`${root}/static/navbar.json`, async navbarItems => {
        const isLoggedIn = Object.keys(authInfo).length && authInfo["auth_method"] != "guest";

        const offsetTop = navbar.find("#offset-top");
        const offsetBottom = navbar.find("#offset-bottom");
        const navbarSeperator = navbar.find("#navbar-seperator");
        for (const item of navbarItems) {
            if ((item["auth_req"] == 1 && !isLoggedIn) ||
                (item["auth_req"] == 2 && isLoggedIn)) continue;
    
            const navItemTemplate = navItem.clone();
            const navText = navItemTemplate.find("a");
            if (item["path"] == window.location.pathname.split("/")[1]) navText.addClass("active");
    
            navText.attr("href", root + "/" + item["path"]);
            navText.find("i").addClass(item["icon"])

            navText.append(item["label"])
    
            if (item["side"] == "top") {
                offsetTop.append(navItemTemplate.clone());
                navItemTemplate.insertBefore(navbarSeperator);
            }
            else {
                offsetBottom.append(navItemTemplate.clone());
                navItemTemplate.insertAfter(navbarSeperator);
            }
        };
        $("body").prepend(navbar);
    });
}
loadAuthInfo().then(loadNavbar);