import { defineConfig } from 'vitepress'
import { withMermaid } from "vitepress-plugin-mermaid";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Deadend CLI",
  description: "Security analysis using code indexing and Language Models",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/deadend-cli' },
      { text: 'Docs', link: '/deadend-cli/markdown-examples' }
    ],

    sidebar: [
      {
        text: 'Get started',
        collapsed: true,
        items: [
          { text: 'Introduction', link: '/introduction' },
          { text: 'Install', link: '/installation' },
          { text: 'first target', link: '/first-target' },
          { text: 'Usage', link: '/usage' },
          { text: 'Features', link: '/features'}
        ]
      },
      {
        text: 'Architecture',
        collapsed: true,
        items: [
          { text: 'Web resource extractor', link: '/architecture/web_extractor' },
          { text: 'Runtime API Examples', link: '/api-examples' }
        ]
      }, 
      {
        text: 'Eval & Benchmarks',
        collapsed: true,
        items: [
          { text: 'Web resource extractor', link: '/architecture/web_extractor' },
          { text: 'Runtime API Examples', link: '/api-examples' }
        ]
      },
      {
        text: 'Research',
        collapsed: true,
        items: [
          { text: 'Web resource extractor', link: '/architecture/web_extractor' },
          { text: 'Runtime API Examples', link: '/api-examples' }
        ]
      }
    ],
    footer: {
      message: 'Hack hack hack',
      copyright: 'Copyright © 2025'
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    ]
  },
  mermaid: {

    },
    mermaidPlugin: {
      class: "mermaid", // set additional css classes for parent container 
    },
})
