import { useEffect, useState } from 'react';
import { Link } from "react-router-dom";
import '../style/App.css';

function WaveIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 12h2l2-7 3 14 3-11 2 7 3-4h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MicIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="9" y="2" width="6" height="12" rx="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v4M8 22h8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function BulbIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M9 18h6M10 22h4M12 2a6 6 0 0 0-4 10.5c.6.6 1 1.4 1 2.3V16h6v-1.2c0-.9.4-1.7 1-2.3A6 6 0 0 0 12 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  );
}

function TagIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M20.6 12.3 12.7 20.2a2 2 0 0 1-2.8 0l-6-6a2 2 0 0 1 0-2.8L11.8 3.4a2 2 0 0 1 1.4-.6H19a2 2 0 0 1 2 2v5.1a2 2 0 0 1-.4 1.4Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <circle cx="15.5" cy="8.5" r="1.4" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function UsersIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="9" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.6" />
      <path d="M2.8 20c.7-3.4 3.3-5.5 6.2-5.5s5.5 2.1 6.2 5.5M16 8.2a3.2 3.2 0 1 1 3 4.4M18 14.7c2.4.4 4.2 2.2 4.8 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

const NAV_LINKS = [
  { href: '#about', label: 'About' },
  { href: '#how', label: 'How it Works' },
  { href: '#usecases', label: 'Use Cases' },
  { href: '#team', label: 'Team' },
  { href: '#contact', label: 'Contact' },
];

const PILLARS = [
  'Conversations carry more than words — tone, pace and context matter too',
  'Turning live speech into structured meaning is still an unsolved problem',
  'Rare or technical terms are where listeners get left behind',
  'Real-time delivery is the difference between insight and hindsight',
];

const CAPABILITIES = [
  {
    icon: MicIcon,
    title: 'Live Capture',
    body: 'SummarizeIT listens in real time, transcribing speech the moment it happens with no lag between the room and the record.',
  },
  {
    icon: TagIcon,
    title: 'Keyword Detection',
    body: 'An evolving dataset of uncommon and domain-specific terms is flagged the instant it surfaces in conversation.',
  },
  {
    icon: BulbIcon,
    title: 'Contextual Summaries',
    body: 'Instead of a wall of transcript, you get short, situational explanations built for the exact moment you needed them.',
  },
];

const USE_CASES = [
  { title: 'Interviews', body: 'Follow unfamiliar technical terms a candidate raises and formulate sharper follow-up questions in the moment.' },
  { title: 'Meetings', body: 'Stay oriented across fast-moving discussions without breaking focus to search for context.' },
  { title: 'Lectures', body: 'Catch dense or unfamiliar terminology as it is introduced, without losing the thread of the lesson.' },
  { title: 'Conferences', body: 'Move between talks and speakers confidently, even outside your own area of expertise.' },
  { title: 'Panel Discussions', body: 'Track cross-references between multiple speakers as the conversation branches and returns.' },
  { title: 'Negotiations', body: 'Understand jargon-heavy exchanges as they unfold so nothing gets agreed to unclearly.' },
];

export default function App() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <>
      {/* Navbar */}
      <header className={`si-nav ${scrolled ? 'si-nav--scrolled' : ''}`}>
        <div className="si-nav__inner">
          <a href="#top" className="si-nav__brand">
            <WaveIcon className="si-nav__brand-icon" />
            SummarizeIT
          </a>
          <nav className={`si-nav__links ${menuOpen ? 'si-nav__links--open' : ''}`}>
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} onClick={() => setMenuOpen(false)}>
                {link.label}
              </a>
            ))}
          </nav>
          <Link to="/dashboard" className="si-btn si-btn--primary">Get Started</Link>
          {/* <a href="#launch" className="si-nav__cta">Get Started</a> */}
          <button
            className="si-nav__toggle"
            aria-label="Toggle navigation menu"
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </header>

      {/* Hero */}
      <section id="top" className="si-hero">
        <div className="si-hero__waveform" aria-hidden="true">
          {Array.from({ length: 48 }).map((_, i) => (
            <span key={i} style={{ animationDelay: `${(i % 12) * 0.09}s` }} />
          ))}
        </div>
        <div className="si-hero__content">
          <p className="si-eyebrow">Record · Transcribe · Summarize</p>
          <h1 className="si-hero__title">
            Never lose the thread<br />of a conversation again
          </h1>
          <p className="si-hero__subtitle">
            SummarizeIT listens in real time and turns unfamiliar terms, dense jargon,
            and fast-moving discussion into short, contextual summaries — right when you need them.
          </p>
          <div className="si-hero__actions">
            <a href="#launch" className="si-btn si-btn--primary">Get Started</a>
            <a href="#about" className="si-btn si-btn--ghost">See how it works</a>
          </div>
        </div>
      </section>

      {/* About  */}
      <section id="about" className="si-section">
        <div className="si-section__grid">
          <div className="si-section__text">
            <p className="si-eyebrow">About SummarizeIT</p>
            <h2>What is SummarizeIT?</h2>
            <p className="si-lede">
              An AI-powered listening layer that converts live conversation into structured,
              contextual summaries — so you're never a beat behind.
            </p>
            <p>
              Speech recognition, natural language processing and machine learning work together
              to understand what's actually being said, not just to record it. Rather than
              handing you long transcripts to sift through afterward, SummarizeIT delivers short,
              situational insight while the conversation is still happening.
            </p>
            <ul className="si-pillars">
              {PILLARS.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </div>
          <div className="si-section__visual">
            <div className="si-panel">
              <MicIcon className="si-panel__icon" />
              <div className="si-panel__transcript">
                <span className="si-chip">Record</span>
                <span className="si-chip">Transcribe</span>
                <span className="si-chip">Tokenise</span>
                <span className="si-chip">Summarise</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="si-section si-section--muted">
        <div className="si-section__grid si-section__grid--reverse">
          <div className="si-section__visual">
            <div className="si-panel si-panel--alt">
              <BulbIcon className="si-panel__icon" />
              <p className="si-panel__caption">
                "...the market shows clear <strong>stochastic volatility</strong>..."
              </p>
              <div className="si-panel__summary">
                Stochastic volatility: a model where an asset's volatility itself
                changes randomly over time, rather than staying fixed.
              </div>
            </div>
          </div>
          <div className="si-section__text">
            <p className="si-eyebrow">How it Works</p>
            <h2>What does it do?</h2>
            <p className="si-lede">
              SummarizeIT records conversations in real time and turns them into
              real-time insight, drawn from a rich, evolving dataset of uncommon terms.
            </p>
            <p>
              Ever been stuck in a conversation where everyone around you understands
              exactly what's being discussed — and you don't? SummarizeIT listens
              continuously, matches what it hears against its keyword dataset, and
              surfaces a short explanation the moment an unfamiliar term appears —
              so when it's your turn to speak, you're already caught up.
            </p>
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="si-section">
        <div className="si-section__header si-section__header--center">
          <p className="si-eyebrow">Capabilities</p>
          <h2>Built for real-time understanding</h2>
        </div>
        <div className="si-cards">
          {CAPABILITIES.map(({ icon: Icon, title, body }) => (
            <div className="si-card" key={title}>
              <Icon className="si-card__icon" />
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Use Cases */}
      <section id="usecases" className="si-section si-section--muted">
        <div className="si-section__header">
          <p className="si-eyebrow">Where it Fits</p>
          <h2>Where it can be used</h2>
          <p className="si-lede">
            Anywhere unfamiliar terms show up faster than you can look them up.
          </p>
        </div>
        <div className="si-usecase-grid">
          {USE_CASES.map((uc) => (
            <div className="si-usecase" key={uc.title}>
              <h3>{uc.title}</h3>
              <p>{uc.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Team */}
      <section id="team" className="si-section">
        <div className="si-section__header si-section__header--center">
          <p className="si-eyebrow">Who's Behind It</p>
          <h2>Team</h2>
          <p className="si-lede">
            A small team building the listening layer for every conversation you're part of.
          </p>
        </div>
        <div className="si-team-placeholder">
          <UsersIcon className="si-team-placeholder__icon" />
          <p>Team profiles coming soon.</p>
        </div>
      </section>

      {/* Contact */}
      <section id="contact" className="si-contact">
        <p className="si-eyebrow si-eyebrow--light">Get in Touch</p>
        <h2>Interested in AI-powered summarization?</h2>
        <p className="si-lede si-lede--light">Let's collaborate.</p>
        <div className="si-social">
          <a href="#" aria-label="Facebook">FB</a>
          <a href="#" aria-label="Instagram">IG</a>
          <a href="#" aria-label="Twitter">TW</a>
          <a href="#" aria-label="LinkedIn">IN</a>
        </div>
      </section>

      {/* Footer */}
      <footer className="si-footer">
        <div className="si-footer__brand">
          <WaveIcon className="si-nav__brand-icon" />
          SummarizeIT
        </div>
        <p>Powered by <a href="https://github.com/Imrkraghu/" target="_blank" rel="noreferrer">imrkraghu</a></p>
      </footer>
    </>
  );
}