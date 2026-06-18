'use client';

import { useState } from 'react';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoButton } from '@/components/ui/NeoButton';
import { t } from '@/lib/i18n';
import { searchWiki, type WikiResult } from '@/lib/api';
import { Search, BookOpen, ExternalLink } from 'lucide-react';

export default function WikiPage() {
  const { lang } = useLang();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<WikiResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchWiki(q);
      setResults(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('error', lang));
      setResults([]);
    } finally {
      setLoading(false);
      setSearched(true);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('tradingWiki', lang)}</h2>

      <NeoCard>
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={t('searchPlaceholder', lang)}
            className="flex-1 border-[3px] border-neo-stroke px-4 py-3 bg-neo-surface font-mono"
          />
          <NeoButton onClick={handleSearch} disabled={loading}>
            <Search size={18} className="mr-2" />
            {loading ? t('loading', lang) : t('search', lang)}
          </NeoButton>
        </div>
      </NeoCard>

      {error && (
        <NeoCard>
          <p className="text-neo-bearish font-bold py-4">{error}</p>
        </NeoCard>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((r) => (
            <NeoCard key={r.id} title={r.title}>
              <div className="flex items-center gap-3 mb-3 flex-wrap">
                <span className="flex items-center gap-1 text-sm font-mono text-neo-muted">
                  <BookOpen size={16} /> {(r.score * 100).toFixed(1)}%
                </span>
                {r.source_url && (
                  <a
                    href={r.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm font-bold text-neo-primary hover:underline"
                  >
                    <ExternalLink size={14} /> {t('source', lang)}
                  </a>
                )}
              </div>
              <p className="text-neo-text leading-relaxed whitespace-pre-line">
                {r.content.slice(0, 600)}
                {r.content.length > 600 ? '…' : ''}
              </p>
            </NeoCard>
          ))}
        </div>
      )}

      {!loading && results.length === 0 && (
        <NeoCard>
          <div className="text-center py-12 text-neo-muted">
            <BookOpen size={48} className="mx-auto mb-4" />
            <p className="font-bold uppercase">
              {searched && !error ? t('noResults', lang) : t('tradingWiki', lang)}
            </p>
            <p className="text-sm mt-2">{t('searchPlaceholder', lang)}</p>
          </div>
        </NeoCard>
      )}
    </div>
  );
}
