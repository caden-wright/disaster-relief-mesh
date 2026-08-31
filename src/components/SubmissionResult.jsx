import { Link } from "react-router-dom";
import "./SubmissionResult.css";

function SubmissionResult({ status = "received", onReset }) {

    const content = {
        received: {
            icon: "✓",
            title: "Submission Received",
            message:
                "This Help Point has received your submission. Delivery to Incident Command has not yet been confirmed."
        },

        sent: {
            icon: "✓",
            title: "Sent to Mesh Network",
            message:
                "A mesh path was available and your submission was sent. This does not guarantee that emergency personnel have received or acted on it."
        },

        queued: {
            icon: "↻",
            title: "Submission Queued",
            message:
                "No mesh path is currently available. This Help Point has saved your submission and will retry when connectivity becomes available."
        },

        error: {
            icon: "!",
            title: "Submission Not Accepted",
            message:
                "The Help Point could not accept your submission. Please try again."
        }
    };

    const result = content[status] || content.received;

    return (
        <div
            className="result-card"
            role="status"
            aria-live="polite"
        >

            <div className={`result-icon result-${status}`}>
                {result.icon}
            </div>

            <h2>{result.title}</h2>

            <p className="result-message">
                {result.message}
            </p>

            <div className="result-warning">
                <strong>Important</strong>

                <p>
                    MeshAid is a supplemental communication system.
                    It does not replace 911 or official emergency services.
                </p>
            </div>

            <div className="result-actions">

                {onReset && (
                    <button
                        className="submit-button"
                        onClick={onReset}
                    >
                        Submit Another
                    </button>
                )}

                <Link to="/" className="back-button">
                    Return to Home
                </Link>

            </div>

        </div>
    );
}

export default SubmissionResult;