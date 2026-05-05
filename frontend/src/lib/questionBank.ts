import type { Question } from "@/lib/api";

/**
 * Static question bank to avoid cold-start lag on first click.
 * The backend still validates and scores; this is the UI source of truth for rendering.
 */
export const QUESTION_BANK: Question[] = [
  {
    id: "q1",
    section: "Analytical Data",
    order: 1,
    text: "Do you have HPLC purity data for your drug substance?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "in_progress", label: "In Progress" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q2",
    section: "Analytical Data",
    order: 2,
    text: "Is your analytical data stored in a tamper-proof system?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
      { id: "dont_know", label: "Don't Know" },
    ],
  },
  {
    id: "q3",
    section: "Analytical Data",
    order: 3,
    text: "Have you validated your analytical methods per ICH Q2(R2)?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "partial", label: "Partial" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q4",
    section: "Analytical Data",
    order: 4,
    text: "Do you have complete audit trails for data transformations?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
      { id: "dont_know", label: "Don't Know" },
    ],
  },
  {
    id: "q5",
    section: "Analytical Data",
    order: 5,
    text: "Can you generate an audit package in under 1 hour?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q6",
    section: "CMC Documentation",
    order: 6,
    text: "Have you drafted ICH M4Q Section 3.2.S (Drug Substance)?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "partial", label: "Partial" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q7",
    section: "CMC Documentation",
    order: 7,
    text: "Are your CMC sections version-controlled?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q8",
    section: "CMC Documentation",
    order: 8,
    text: "Have you linked analytical data to CMC sections?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
      { id: "dont_know", label: "Don't Know" },
    ],
  },
  {
    id: "q9",
    section: "CMC Documentation",
    order: 9,
    text: "Is your CMC documentation eCTD-ready?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
      { id: "dont_know", label: "Don't Know" },
    ],
  },
  {
    id: "q10",
    section: "CMC Documentation",
    order: 10,
    text: "Have you had a pre-IND meeting with FDA?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "scheduled", label: "Scheduled" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q11",
    section: "Regulatory Strategy",
    order: 11,
    text: "Have you mapped your therapeutic to ICH/FDA requirements?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "partial", label: "Partial" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q12",
    section: "Regulatory Strategy",
    order: 12,
    text: "Do you have a regulatory consultant or in-house RA team?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
    ],
  },
  {
    id: "q13",
    section: "Regulatory Strategy",
    order: 13,
    text: "How many months until IND submission?",
    options: [
      { id: "0_6", label: "0–6" },
      { id: "6_12", label: "6–12" },
      { id: "12_18", label: "12–18" },
      { id: "18_plus", label: "18+" },
    ],
  },
  {
    id: "q14",
    section: "Regulatory Strategy",
    order: 14,
    text: "Have you identified all missing evidence?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
      { id: "dont_know", label: "Don't Know" },
    ],
  },
  {
    id: "q15",
    section: "Regulatory Strategy",
    order: 15,
    text: "Do you have a risk mitigation plan for regulatory blockers?",
    options: [
      { id: "yes", label: "Yes" },
      { id: "no", label: "No" },
    ],
  },
];

