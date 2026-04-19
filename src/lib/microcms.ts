import { createClient } from 'microcms-js-sdk';

export const client = createClient({
  serviceDomain: 'uzpj3q81dc',
  apiKey: 'gkRJZrpd0NaT35zJp1BB4KwTA9qyebfG0iWK',
});

export type Blog = {
  id: string;
  title: string;
  content: string;
  eyecatch?: { url: string; height: number; width: number };
  category?: { id: string; name: string };
  publishedAt: string;
};
