import BeaconAssessment from "@/components/BeaconAssessment";

export default function Home() {
  return (
    <div className="min-h-full flex flex-col">
      <main className="flex-1">
        <BeaconAssessment />
      </main>
      <footer className="border-t border-[var(--beacon-border)] bg-white/60 py-6 text-center text-xs text-[var(--beacon-muted)] backdrop-blur-sm">
        For educational planning purposes only — not legal or regulatory advice.
      </footer>
    </div>
  );
}
