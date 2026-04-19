import { createClient } from 'microcms-js-sdk';

export const client = createClient({
  serviceDomain: 'uzpj3q81dc',
  apiKey: import.meta.env.MICROCMS_API_KEY,
});

export type Blog = {
  id: string;
  title: string;
  content: string;
  eyecatch?: { url: string; height: number; width: number };
  category?: { id: string; name: string };
  publishedAt: string;
};
