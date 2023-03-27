async function apiRequest(route, json=null, method="POST") {
    return fetch(`/api/${route}`, {
            method: method,
            body: JSON.stringify(json),
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        }
    );
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }