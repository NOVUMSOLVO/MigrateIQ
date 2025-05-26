import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Import translation files
import enTranslations from './locales/en.json';
import esTranslations from './locales/es.json';
import frTranslations from './locales/fr.json';
import deTranslations from './locales/de.json';
import zhTranslations from './locales/zh.json';
import jaTranslations from './locales/ja.json';
import arTranslations from './locales/ar.json';
import heTranslations from './locales/he.json';

const resources = {
  en: { translation: enTranslations },
  es: { translation: esTranslations },
  fr: { translation: frTranslations },
  de: { translation: deTranslations },
  zh: { translation: zhTranslations },
  ja: { translation: jaTranslations },
  ar: { translation: arTranslations },
  he: { translation: heTranslations },
};

// Language detection options
const detectionOptions = {
  // Order of language detection
  order: ['localStorage', 'navigator', 'htmlTag', 'path', 'subdomain'],
  
  // Keys to lookup language from
  lookupLocalStorage: 'migrateiq_language',
  lookupFromPathIndex: 0,
  lookupFromSubdomainIndex: 0,
  
  // Cache user language
  caches: ['localStorage'],
  
  // Don't convert country code to language code
  convertDetectedLanguage: (lng) => lng.split('-')[0],
};

i18n
  // Load translation using http backend
  .use(Backend)
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    resources,
    
    // Default language
    fallbackLng: 'en',
    
    // Debug mode (disable in production)
    debug: process.env.NODE_ENV === 'development',
    
    // Language detection
    detection: detectionOptions,
    
    // Interpolation options
    interpolation: {
      escapeValue: false, // React already escapes values
      formatSeparator: ',',
      format: function(value, format, lng) {
        if (format === 'uppercase') return value.toUpperCase();
        if (format === 'lowercase') return value.toLowerCase();
        if (format === 'capitalize') return value.charAt(0).toUpperCase() + value.slice(1);
        return value;
      }
    },
    
    // React options
    react: {
      useSuspense: false,
      bindI18n: 'languageChanged',
      bindI18nStore: '',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em', 'span'],
    },
    
    // Backend options for loading translations
    backend: {
      loadPath: '/locales/{{lng}}.json',
      addPath: '/locales/add/{{lng}}/{{ns}}',
      allowMultiLoading: false,
      crossDomain: false,
      withCredentials: false,
      overrideMimeType: false,
      requestOptions: {
        mode: 'cors',
        credentials: 'same-origin',
        cache: 'default',
      },
    },
    
    // Namespace and key separator
    ns: ['translation'],
    defaultNS: 'translation',
    keySeparator: '.',
    nsSeparator: ':',
    
    // Pluralization
    pluralSeparator: '_',
    contextSeparator: '_',
    
    // Missing key handling
    saveMissing: process.env.NODE_ENV === 'development',
    missingKeyHandler: (lng, ns, key, fallbackValue) => {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Missing translation key: ${key} for language: ${lng}`);
      }
    },
    
    // Post processing
    postProcess: ['interval', 'plural'],
    
    // Clean code on production
    cleanCode: true,
    
    // Return objects for complex translations
    returnObjects: true,
    
    // Return empty string for empty values
    returnEmptyString: false,
    
    // Return null for missing keys
    returnNull: false,
    
    // Join arrays
    joinArrays: false,
    
    // Override language codes
    load: 'languageOnly',
    preload: ['en'],
    
    // Whitelist languages
    supportedLngs: ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ar', 'he'],
    nonExplicitSupportedLngs: false,
    
    // Check for supported languages
    checkForDefaultNamespace: false,
    
    // Append namespace to missing key
    appendNamespaceToMissingKey: false,
    
    // Parse missing key handler
    parseMissingKeyHandler: (key) => key,
    
    // Ignore JSON structure
    ignoreJSONStructure: true,
  });

// Export language utilities
export const changeLanguage = (lng) => {
  return i18n.changeLanguage(lng);
};

export const getCurrentLanguage = () => {
  return i18n.language;
};

export const getSupportedLanguages = () => {
  return [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'es', name: 'Spanish', nativeName: 'Español' },
    { code: 'fr', name: 'French', nativeName: 'Français' },
    { code: 'de', name: 'German', nativeName: 'Deutsch' },
    { code: 'zh', name: 'Chinese', nativeName: '中文' },
    { code: 'ja', name: 'Japanese', nativeName: '日本語' },
    { code: 'ar', name: 'Arabic', nativeName: 'العربية' },
    { code: 'he', name: 'Hebrew', nativeName: 'עברית' },
  ];
};

export const isRTL = (lng = getCurrentLanguage()) => {
  return ['ar', 'he'].includes(lng);
};

export default i18n;
