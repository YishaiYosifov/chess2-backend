async function apiRequest(route, json=null, method="POST") {
    const response = await fetch(`/api/${route}`, {
            method: method,
            body: JSON.stringify(json),
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        }
    );

    const responseCopy = response.clone();
    if (responseCopy.status == 401 && await responseCopy.text() == "Session Expired") {
        window.location.replace("/login?a=session-expired");
        throw new Error("Session Token Expired");
    }
    
    return response;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }