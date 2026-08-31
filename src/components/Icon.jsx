function Icon({ name, size = 24 }) {
    const common = {
        width: size,
        height: size,
        viewBox: "0 0 24 24",
        fill: "none",
        stroke: "currentColor",
        strokeWidth: "2",
        strokeLinecap: "round",
        strokeLinejoin: "round",
        "aria-hidden": "true"
    };

    const icons = {
        medical: (
            <svg {...common}>
                <path d="M12 5v14" />
                <path d="M5 12h14" />
            </svg>
        ),

        check: (
            <svg {...common}>
                <path d="M20 6 9 17l-5-5" />
            </svg>
        ),

        resources: (
            <svg {...common}>
                <path d="M6 7h12" />
                <path d="M6 12h12" />
                <path d="M6 17h12" />
                <circle cx="3" cy="7" r="1" />
                <circle cx="3" cy="12" r="1" />
                <circle cx="3" cy="17" r="1" />
            </svg>
        ),

        messages: (
            <svg {...common}>
                <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z" />
            </svg>
        ),

        warning: (
            <svg {...common}>
                <path d="M10.3 2.9 1.8 17a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 2.9a2 2 0 0 0-3.4 0z" />
                <path d="M12 9v4" />
                <path d="M12 17h.01" />
            </svg>
        ),

        home: (
            <svg {...common}>
                <path d="m3 11 9-8 9 8" />
                <path d="M5 10v10h14V10" />
                <path d="M9 20v-6h6v6" />
            </svg>
        )
    };

    return icons[name] || null;
}

export default Icon;