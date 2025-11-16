#!/usr/bin/env python3
"""
Philosophical Traditions

Defines real philosophical traditions with their core commitments,
methodologies, and incompatibilities.

These traditions provide genuine philosophical identities for agents,
rather than designer positions optimized for specific passages.
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PhilosophicalTradition:
    """A real philosophical tradition with genuine commitments"""
    name: str
    core_commitments: List[str]
    key_figures: List[str]
    methodological_principles: List[str]
    characteristic_concerns: List[str]
    typical_blindspots: List[str]
    incompatible_with: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary for LLM prompts"""
        return {
            'name': self.name,
            'core_commitments': self.core_commitments,
            'key_figures': self.key_figures,
            'methods': self.methodological_principles,
            'concerns': self.characteristic_concerns,
            'blindspots': self.typical_blindspots,
            'incompatible_with': self.incompatible_with
        }


# Define major philosophical traditions with genuine incompatibilities
TRADITIONS = [
    PhilosophicalTradition(
        name="Heideggerian Phenomenology",
        core_commitments=[
            "Being-in-the-world is ontologically primary",
            "Dasein's being is care and temporality",
            "Meaning emerges through existential engagement, not representational correspondence",
            "Authenticity requires confronting thrownness and finitude"
        ],
        key_figures=[
            "Martin Heidegger",
            "Hans-Georg Gadamer",
            "Maurice Merleau-Ponty"
        ],
        methodological_principles=[
            "Hermeneutic interpretation (understanding through the hermeneutic circle)",
            "Existential analysis of Dasein's modes of being",
            "Phenomenological description that brackets scientific assumptions",
            "Attention to pre-theoretical engagement with world"
        ],
        characteristic_concerns=[
            "The meaning of Being",
            "Authentic vs inauthentic existence",
            "Temporality and historicity",
            "The limits of calculative thinking"
        ],
        typical_blindspots=[
            "Dismisses analytic precision as missing the point",
            "Can undervalue empirical investigation",
            "May romanticize pre-modern or pre-scientific perspectives",
            "Difficult to engage with naturalistic frameworks"
        ],
        incompatible_with=[
            "Subject-object metaphysics",
            "Ahistorical analysis",
            "Reductive naturalism",
            "Representationalist epistemology"
        ]
    ),

    PhilosophicalTradition(
        name="Analytic Pragmatism",
        core_commitments=[
            "Truth is what is vindicated through inquiry and practical consequences",
            "Philosophy is continuous with empirical science",
            "Meaning is use; concepts are tools for navigation",
            "Inquiry is experimental, fallibilist, and self-correcting"
        ],
        key_figures=[
            "John Dewey",
            "W.V.O. Quine",
            "Wilfrid Sellars",
            "Robert Brandom"
        ],
        methodological_principles=[
            "Naturalistic analysis (no sharp fact/value or is/ought divide)",
            "Inferentialist semantics (meaning as role in inference)",
            "Experimental reasoning and hypothesis testing",
            "Dissolving traditional problems through conceptual analysis"
        ],
        characteristic_concerns=[
            "How inquiry actually works",
            "The relationship between norms and nature",
            "Making implicit commitments explicit",
            "Democratic participation in knowledge production"
        ],
        typical_blindspots=[
            "Can be too quick to dismiss 'merely' metaphysical questions",
            "May undervalue phenomenological texture",
            "Sometimes conflates what works with what's true",
            "Can miss existential dimensions of meaning"
        ],
        incompatible_with=[
            "Pure phenomenology divorced from practice",
            "Foundationalism (given, self-justifying truths)",
            "A priori metaphysics",
            "Radical skepticism"
        ]
    ),

    PhilosophicalTradition(
        name="Post-Structuralism",
        core_commitments=[
            "Meaning is differential, relational, and fundamentally unstable",
            "Power relations structure discourse and knowledge",
            "Binary oppositions conceal hierarchies and exclusions",
            "Presence and origins are illusory; there is only play of différance"
        ],
        key_figures=[
            "Jacques Derrida",
            "Michel Foucault",
            "Gilles Deleuze",
            "Judith Butler"
        ],
        methodological_principles=[
            "Deconstruction (revealing internal contradictions and aporias)",
            "Genealogical analysis (uncovering contingent historical construction)",
            "Attention to margins, ruptures, and what is excluded",
            "Suspicion of totalizing narratives and unified subjects"
        ],
        characteristic_concerns=[
            "How meaning escapes authorial intention",
            "The violence of conceptual systems",
            "Resistance and subversion",
            "The instability of identity"
        ],
        typical_blindspots=[
            "Can struggle to make positive claims",
            "May overemphasize textuality at expense of material conditions",
            "Sometimes difficult to engage with empirical questions",
            "Risk of performative contradiction in critiquing all foundations"
        ],
        incompatible_with=[
            "Stable, determinate meaning",
            "Unified subjectivity",
            "Linear progress narratives",
            "Transparent communication"
        ]
    ),

    PhilosophicalTradition(
        name="Analytic Naturalism",
        core_commitments=[
            "Philosophy is continuous with natural science",
            "All phenomena supervene on physical facts",
            "Explanations should be mechanistic and causally tractable",
            "Logic and conceptual analysis are primary philosophical tools"
        ],
        key_figures=[
            "Bertrand Russell",
            "Rudolf Carnap",
            "David Lewis",
            "Frank Jackson"
        ],
        methodological_principles=[
            "Formal logic and rigorous argument",
            "Conceptual analysis and clarification",
            "Empirical verification where possible",
            "Parsimony (Occam's razor)"
        ],
        characteristic_concerns=[
            "Mind-body problem",
            "Reference and truth conditions",
            "Possibility and necessity",
            "Reducing complex phenomena to simpler components"
        ],
        typical_blindspots=[
            "Can dismiss Continental philosophy as obscurantism",
            "May miss holistic or emergent phenomena",
            "Sometimes ignores historical/cultural context",
            "Can struggle with normative/evaluative questions"
        ],
        incompatible_with=[
            "Appeals to irreducible phenomenology",
            "Rejection of bivalence or classical logic",
            "Anti-realism about truth",
            "Mysticism or ineffability"
        ]
    ),

    PhilosophicalTradition(
        name="Process Philosophy",
        core_commitments=[
            "Becoming is more fundamental than being",
            "Reality is constituted by events and processes, not substances",
            "Experience goes all the way down (panpsychism or panexperientialism)",
            "All actualities are constituted by their relations"
        ],
        key_figures=[
            "Alfred North Whitehead",
            "Charles Hartshorne",
            "William James (radical empiricism)"
        ],
        methodological_principles=[
            "Speculative metaphysics grounded in experience",
            "Coherence and adequacy to all domains of experience",
            "Attention to creative advance and novelty",
            "Integration of science and value"
        ],
        characteristic_concerns=[
            "The nature of time and change",
            "How novelty enters the world",
            "Mind-matter continuity",
            "God and cosmic creativity"
        ],
        typical_blindspots=[
            "Can be overly systematic and totalizing",
            "May anthropomorphize nature",
            "Sometimes difficult to test empirically",
            "Can downplay stable structures"
        ],
        incompatible_with=[
            "Substance metaphysics",
            "Purely mechanistic worldviews",
            "Eliminativist views of experience",
            "Static conceptions of reality"
        ]
    ),

    PhilosophicalTradition(
        name="Marxist Materialism",
        core_commitments=[
            "Material conditions and economic relations are primary",
            "Consciousness is shaped by social being",
            "History is driven by class struggle",
            "Ideology mystifies and legitimates domination"
        ],
        key_figures=[
            "Karl Marx",
            "Georg Lukács",
            "Antonio Gramsci",
            "Theodor Adorno"
        ],
        methodological_principles=[
            "Dialectical analysis of contradictions",
            "Ideology critique",
            "Historical materialism",
            "Praxis (unity of theory and practice)"
        ],
        characteristic_concerns=[
            "Alienation and exploitation",
            "False consciousness",
            "Revolutionary transformation",
            "The relationship between base and superstructure"
        ],
        typical_blindspots=[
            "Can be economically reductionist",
            "May undervalue cultural and symbolic dimensions",
            "Sometimes teleological about historical progress",
            "Can dismiss non-class forms of oppression"
        ],
        incompatible_with=[
            "Idealist metaphysics",
            "Methodological individualism",
            "Ahistorical analysis",
            "Liberal neutrality"
        ]
    ),

    PhilosophicalTradition(
        name="Virtue Ethics (Neo-Aristotelian)",
        core_commitments=[
            "Ethics concerns character and human flourishing, not just actions",
            "Virtues are excellences that constitute the good life",
            "Practical wisdom (phronesis) is irreducible to rule-following",
            "Human nature provides normative standards"
        ],
        key_figures=[
            "Aristotle",
            "Philippa Foot",
            "Alasdair MacIntyre",
            "Rosalind Hursthouse"
        ],
        methodological_principles=[
            "Eudaimonistic inquiry (what promotes flourishing)",
            "Attention to particulars and practical judgment",
            "Narrative understanding of lives",
            "Emphasis on moral education and habituation"
        ],
        characteristic_concerns=[
            "What makes a life good",
            "The unity of the virtues",
            "Moral development",
            "Community and tradition"
        ],
        typical_blindspots=[
            "Can be conservative about social change",
            "May struggle with moral dilemmas",
            "Sometimes too quick to appeal to 'human nature'",
            "Can undervalue individual rights"
        ],
        incompatible_with=[
            "Pure consequentialism",
            "Kantian deontology",
            "Moral relativism",
            "Anti-naturalism in ethics"
        ]
    ),

    PhilosophicalTradition(
        name="Skeptical Empiricism (Humean)",
        core_commitments=[
            "All knowledge derives from sensory experience",
            "Causation is just constant conjunction, not necessary connection",
            "The self is a bundle of perceptions, not a substance",
            "Reason is slave to the passions"
        ],
        key_figures=[
            "David Hume",
            "Bas van Fraassen",
            "P.F. Strawson (descriptive metaphysics)"
        ],
        methodological_principles=[
            "Careful attention to what experience actually delivers",
            "Skepticism about unobservable entities and necessary connections",
            "Naturalistic account of belief formation",
            "Distinction between matters of fact and relations of ideas"
        ],
        characteristic_concerns=[
            "The problem of induction",
            "Limits of reason",
            "Projection of internal impressions onto world",
            "Custom and habit in belief"
        ],
        typical_blindspots=[
            "Can be too skeptical about theoretical entities",
            "May undervalue rational agency",
            "Sometimes struggles to explain normativity",
            "Can lead to excessive conservatism"
        ],
        incompatible_with=[
            "Rationalism and a priori knowledge",
            "Realism about causation",
            "Substantial self",
            "Reason as motive force"
        ]
    )
]


def get_tradition_by_name(name: str) -> PhilosophicalTradition:
    """Get tradition by name"""
    for tradition in TRADITIONS:
        if tradition.name.lower() == name.lower():
            return tradition
    raise ValueError(f"Unknown tradition: {name}")


def get_random_traditions(n: int) -> List[PhilosophicalTradition]:
    """Get n random traditions, ensuring maximal incompatibility"""
    import random

    if n > len(TRADITIONS):
        raise ValueError(f"Only {len(TRADITIONS)} traditions available")

    # For now, just random selection
    # Could add logic to maximize incompatibility
    return random.sample(TRADITIONS, n)


def get_maximally_incompatible_traditions(n: int) -> List[PhilosophicalTradition]:
    """Select n traditions that are maximally incompatible with each other"""
    import random

    if n > len(TRADITIONS):
        raise ValueError(f"Only {len(TRADITIONS)} traditions available")

    if n == 0:
        return []

    # Start with random first tradition
    selected = [random.choice(TRADITIONS)]
    remaining = [t for t in TRADITIONS if t != selected[0]]

    # For each subsequent tradition, prefer ones incompatible with already selected
    for _ in range(n - 1):
        if not remaining:
            break

        # Score each remaining tradition by incompatibility
        def incompatibility_score(tradition):
            score = 0
            for selected_tradition in selected:
                # Count shared incompatibilities (suggests they're in different camps)
                shared_incompatibilities = set(tradition.incompatible_with) & set(selected_tradition.incompatible_with)

                # Check if they're incompatible with each other
                if tradition.name in selected_tradition.incompatible_with or \
                   selected_tradition.name in tradition.incompatible_with:
                    score += 5

                # Check if they have fundamentally different commitments
                if any(keyword in " ".join(tradition.core_commitments).lower()
                       for keyword in ["not", "reject", "beyond", "against"]):
                    score += 1

            return score

        # Sort by incompatibility score
        remaining.sort(key=incompatibility_score, reverse=True)

        # Pick from top candidates with some randomness
        top_candidates = remaining[:min(3, len(remaining))]
        next_tradition = random.choice(top_candidates)

        selected.append(next_tradition)
        remaining = [t for t in remaining if t != next_tradition]

    return selected


if __name__ == "__main__":
    print("Available Philosophical Traditions:")
    print("=" * 80)

    for tradition in TRADITIONS:
        print(f"\n{tradition.name}")
        print(f"  Core commitment: {tradition.core_commitments[0]}")
        print(f"  Key figures: {', '.join(tradition.key_figures[:2])}")
        print(f"  Incompatible with: {', '.join(tradition.incompatible_with[:2])}")

    print("\n" + "=" * 80)
    print("\nTesting maximal incompatibility selection:")
    selected = get_maximally_incompatible_traditions(3)
    print(f"Selected: {[t.name for t in selected]}")
