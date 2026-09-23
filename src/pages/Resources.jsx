import { useState } from "react";
import { Link } from "react-router-dom";
import "./Form.css";
import SubmissionResult from "../components/SubmissionResult";
import { submitMessage } from "../api/helpPoint";

function Resources() {
    const [resource, setResource] = useState("Water");
    const [quantity, setQuantity] = useState("1");
    const [urgency, setUrgency] = useState("Low");
    const [submissionStatus, setSubmissionStatus] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    async function handleSubmit() {
        if (Number(quantity) <= 0) {
            alert("Please enter a valid quantity.");
            return;
        }

        const request = {
            type: "resource_request",
            resource,
            quantity: Number(quantity),
            urgency
        };

        setSubmitting(true);

        try {
            const result = await submitMessage(request);
            setSubmissionStatus(result.status);
        } catch (error) {
            console.error("Resource Request failed:", error);
            setSubmissionStatus("error");
        } finally {
            setSubmitting(false);
        }
    }

    if (submissionStatus) {
        return (
            <div className="page-container">
                <SubmissionResult
                    status={submissionStatus}
                    onReset={() => {
                        setSubmissionStatus(null);
                        setResource("Water");
                        setQuantity("1");
                        setUrgency("Low");
                    }}
                />
            </div>
        );
    }

    return (
        <div className="page-container">
            <header className="page-header">
                <h1 className="page-title">
                    Request Resources
                </h1>

                <p className="page-description">
                    Select the resource your group currently needs.
                </p>
            </header>

            <div className="form-card">

                <div className="form-group">
                    <label>
                        Resource Needed
                    </label>

                    <div
                        className="resource-options"
                        role="radiogroup"
                        aria-label="Resource needed"
                    >
                        {[
                            "Water",
                            "Food",
                            "Medicine",
                            "Shelter"
                        ].map((option) => (
                            <button
                                key={option}
                                type="button"
                                className={
                                    resource === option
                                        ? "resource-option selected"
                                        : "resource-option"
                                }
                                onClick={() =>
                                    setResource(option)
                                }
                                role="radio"
                                aria-checked={
                                    resource === option
                                }
                            >
                                {option}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="form-group">
                    <label htmlFor="quantity">
                        Quantity Needed
                    </label>

                    <input
                        id="quantity"
                        type="number"
                        min="1"
                        value={quantity}
                        onChange={(event) =>
                            setQuantity(event.target.value)
                        }
                        placeholder="Enter quantity"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="urgency">
                        Urgency
                    </label>

                    <select
                        id="urgency"
                        value={urgency}
                        onChange={(event) =>
                            setUrgency(event.target.value)
                        }
                    >
                        <option>Low</option>
                        <option>Medium</option>
                        <option>High</option>
                    </select>
                </div>

                <div className="form-actions">

                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={
                            quantity === "" ||
                            submitting
                        }
                    >
                        {submitting
                            ? "Submitting..."
                            : "Submit Resource Request"}
                    </button>

                    <Link
                        to="/"
                        className="back-button"
                    >
                        Back to Home
                    </Link>

                </div>
            </div>
        </div>
    );
}

export default Resources;