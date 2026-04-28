'use client';

import { useState, useEffect, useMemo } from 'react';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoButton } from '@/components/ui/NeoButton';
import { t } from '@/lib/i18n';
import { Search, BookOpen, Tag, ArrowLeft } from 'lucide-react';

interface WikiConcept {
  id: string;
  title: string;
  source_url: string;
  tags: string[];
  backlinks: string[];
  related_count: number;
  summary: string;
  body_preview: string;
}

interface WikiHub {
  id: string;
  title: string;
  concepts: string[];
}

interface WikiIndex {
  meta: { total_concepts: number; total_hubs: number; version: string };
  concepts: WikiConcept[];
  hubs: WikiHub[];
}

export default function WikiPage() {
  const { lang } = useLang();
  const [index, setIndex] = useState<WikiIndex | null>(null);
  const [query, setQuery] = useState('');
  const [selectedHub, setSelectedHub] = useState<string>('');
  const [selectedConcept, setSelectedConcept] = useState<WikiConcept | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/wiki-index.json')
      .then((r) => r.json())
      .then((data) => {
        setIndex(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filteredConcepts = useMemo(() => {
    if (!index) return [];
    let results = index.concepts;
    if (selectedHub) {
      const hub = index.hubs.find((h) => h.id === selectedHub);
      if (hub) {
        results = results.filter((c) => hub.concepts.includes(c.id));
      }
    }
    if (query.trim()) {
      const q = query.toLowerCase();
      results = results.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.summary.toLowerCase().includes(q) ||
          c.tags.some((t) => t.toLowerCase().includes(q))
      );
    }
    return results;
  }, [index, query, selectedHub]);

  if (selectedConcept) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <NeoButton size="sm" onClick={() => setSelectedConcept(null)}>
            <ArrowLeft size={16} className="mr-1" /> Back
          </NeoButton>
          <h2 className="text-2xl font-black uppercase tracking-wider">{selectedConcept.title}</h2>
        </div>
        <NeoCard>
          <div className="flex items-center gap-2 mb-4">
            <Tag size={16} className="text-neo-accent" />
            <span className="text-sm font-mono text-neo-muted">
              {selectedConcept.related_count} related concepts
            </span>
          </div>
          <div className="prose prose-invert max-w-none">
            <p className="text-neo-text leading-relaxed whitespace-pre-line">
              {selectedConcept.body_preview}
            </p>
          </div>
          {selectedConcept.source_url && (
            <div className="mt-4 pt-4 border-t-2 border-neo-stroke">
              <a
                href={selectedConcept.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-neo-accent font-bold text-sm hover:underline"
              >
                View original source →
              </a>
            </div>
          )}
        </NeoCard>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('tradingWiki', lang)}</h2>

      {/* Search + Stats */}
      <NeoCard>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && setQuery(query)}
              placeholder={t('searchPlaceholder', lang)}
              className="flex-1 border-[3px] border-neo-stroke px-4 py-3 bg-neo-surface font-mono"
            />
            <NeoButton onClick={() => setQuery(query)} disabled={loading}>
              <Search size={18} className="mr-2" />
              {loading ? t('loading', lang) : t('search', lang)}
            </NeoButton>
          </div>
          {index && (
            <div className="flex items-center gap-4 text-sm font-mono text-neo-muted">
              <span>{index.meta.total_concepts} concepts</span>
              <span>{index.meta.total_hubs} categories</span>
            </div>
          )}
        </div>
      </NeoCard>

      {/* Hub Filters */}
      {index && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedHub('')}
            className={`px-3 py-1 text-xs font-bold uppercase border-2 border-neo-stroke ${
              !selectedHub ? 'bg-neo-accent text-white' : 'bg-neo-surface'
            }`}
          >
            All
          </button>
          {index.hubs.map((hub) => (
            <button
              key={hub.id}
              onClick={() => setSelectedHub(hub.id === selectedHub ? '' : hub.id)}
              className={`px-3 py-1 text-xs font-bold uppercase border-2 border-neo-stroke ${
                selectedHub === hub.id ? 'bg-neo-accent text-white' : 'bg-neo-surface'
              }`}
            >
              {hub.title}
            </button>
          ))}
        </div>
      )}

      {/* Results */}
      {filteredConcepts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredConcepts.map((concept) => (
            <NeoCard
              key={concept.id}
              title={concept.title}
              className="cursor-pointer hover:border-neo-accent transition-colors"
              onClick={() => setSelectedConcept(concept)}
            >
              <div className="flex items-center gap-2 mb-2">
                <BookOpen size={14} className="text-neo-muted" />
                <span className="text-xs font-mono text-neo-muted">
                  {concept.related_count} related
                </span>
              </div>
              <p className="text-sm text-neo-text line-clamp-3">{concept.summary}</p>
              {concept.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {concept.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs font-mono bg-neo-bg px-2 py-0.5 border border-neo-stroke"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </NeoCard>
          ))}
        </div>
      ) : (
        <NeoCard>
          <div className="text-center py-12 text-neo-muted">
            <BookOpen size={48} className="mx-auto mb-4" />
            <p className="font-bold uppercase">
              {query ? 'No concepts found' : 'Select a category or search'}
            </p>
          </div>
        </NeoCard>
      )}
    </div>
  );
}
