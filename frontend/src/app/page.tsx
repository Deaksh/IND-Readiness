import BeaconAssessment from "@/components/BeaconAssessment";

export default function Home() {
  return (
    <div className="min-h-full flex flex-col">
      <main className="flex-1">
        <BeaconAssessment />
      </main>
      <footer className="border-t border-[var(--beacon-border)] bg-white/60 px-4 py-6 text-center text-xs leading-relaxed text-[var(--beacon-muted)] backdrop-blur-sm">
        <p>
          <a
            href="https://beacon-bio.carrd.co"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-[var(--beacon-accent)] underline-offset-4 hover:underline"
          >
            beacon-bio.carrd.co
          </a>
        </p>
        <p className="mt-2">
          For educational planning purposes only — not legal or regulatory advice.
        </p>
      </footer>
    </div>
  );
}
