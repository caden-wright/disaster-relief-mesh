export async function getHelpPointStatus() {
    const response = await fetch("/api/status");

    if (!response.ok) {
        throw new Error(`Help Point status failed (${response.status})`);
    }

    return response.json();
}

export async function submitMessage(request) {
    const response = await fetch("/api/messages", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(request)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.detail || `Submission failed (${response.status})`
        );
    }

    return data;
}