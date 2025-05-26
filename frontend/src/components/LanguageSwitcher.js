import React, { useState } from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Box,
  Typography,
  Divider
} from '@mui/material';
import {
  Language as LanguageIcon,
  Check as CheckIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { getSupportedLanguages, isRTL } from '../i18n';

const LanguageSwitcher = ({ variant = 'icon', showLabel = false }) => {
  const { i18n, t } = useTranslation();
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  
  const supportedLanguages = getSupportedLanguages();
  const currentLanguage = i18n.language;

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLanguageChange = async (languageCode) => {
    try {
      await i18n.changeLanguage(languageCode);
      
      // Update document direction for RTL languages
      const isRtl = isRTL(languageCode);
      document.dir = isRtl ? 'rtl' : 'ltr';
      document.documentElement.lang = languageCode;
      
      // Store language preference
      localStorage.setItem('migrateiq_language', languageCode);
      
      // Update page title direction if needed
      if (isRtl) {
        document.body.classList.add('rtl');
      } else {
        document.body.classList.remove('rtl');
      }
      
      handleClose();
    } catch (error) {
      console.error('Failed to change language:', error);
    }
  };

  const getCurrentLanguageName = () => {
    const current = supportedLanguages.find(lang => lang.code === currentLanguage);
    return current ? current.nativeName : 'English';
  };

  const getLanguageFlag = (code) => {
    const flags = {
      en: '🇺🇸',
      es: '🇪🇸',
      fr: '🇫🇷',
      de: '🇩🇪',
      zh: '🇨🇳',
      ja: '🇯🇵',
      ar: '🇸🇦',
      he: '🇮🇱'
    };
    return flags[code] || '🌐';
  };

  if (variant === 'button') {
    return (
      <Box>
        <Tooltip title={t('common.language')}>
          <IconButton
            onClick={handleClick}
            size="small"
            sx={{
              color: 'inherit',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
              }
            }}
            aria-label="language selector"
            aria-controls={open ? 'language-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={open ? 'true' : undefined}
          >
            <LanguageIcon />
            {showLabel && (
              <Typography variant="body2" sx={{ ml: 1 }}>
                {getCurrentLanguageName()}
              </Typography>
            )}
          </IconButton>
        </Tooltip>
        
        <Menu
          id="language-menu"
          anchorEl={anchorEl}
          open={open}
          onClose={handleClose}
          MenuListProps={{
            'aria-labelledby': 'language-button',
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          PaperProps={{
            sx: {
              minWidth: 200,
              maxHeight: 400,
              '& .MuiMenuItem-root': {
                px: 2,
                py: 1
              }
            }
          }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle2" color="text.secondary">
              {t('common.language')}
            </Typography>
          </Box>
          <Divider />
          
          {supportedLanguages.map((language) => (
            <MenuItem
              key={language.code}
              onClick={() => handleLanguageChange(language.code)}
              selected={language.code === currentLanguage}
              sx={{
                direction: isRTL(language.code) ? 'rtl' : 'ltr',
                justifyContent: 'space-between'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                <Typography
                  component="span"
                  sx={{ 
                    fontSize: '1.2em', 
                    mr: isRTL(language.code) ? 0 : 1,
                    ml: isRTL(language.code) ? 1 : 0
                  }}
                >
                  {getLanguageFlag(language.code)}
                </Typography>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {language.nativeName}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {language.name}
                  </Typography>
                </Box>
              </Box>
              
              {language.code === currentLanguage && (
                <ListItemIcon sx={{ minWidth: 'auto', ml: 1 }}>
                  <CheckIcon fontSize="small" color="primary" />
                </ListItemIcon>
              )}
            </MenuItem>
          ))}
        </Menu>
      </Box>
    );
  }

  // Compact variant for mobile or space-constrained areas
  return (
    <Box>
      <Tooltip title={`${t('common.language')}: ${getCurrentLanguageName()}`}>
        <IconButton
          onClick={handleClick}
          size="small"
          sx={{
            color: 'inherit',
            minWidth: 40,
            height: 40,
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }
          }}
          aria-label="language selector"
        >
          <Typography component="span" sx={{ fontSize: '1.2em' }}>
            {getLanguageFlag(currentLanguage)}
          </Typography>
        </IconButton>
      </Tooltip>
      
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
          sx: {
            minWidth: 180,
            '& .MuiMenuItem-root': {
              px: 1.5,
              py: 0.5
            }
          }
        }}
      >
        {supportedLanguages.map((language) => (
          <MenuItem
            key={language.code}
            onClick={() => handleLanguageChange(language.code)}
            selected={language.code === currentLanguage}
            sx={{
              direction: isRTL(language.code) ? 'rtl' : 'ltr'
            }}
          >
            <ListItemIcon sx={{ minWidth: 32 }}>
              <Typography component="span" sx={{ fontSize: '1.1em' }}>
                {getLanguageFlag(language.code)}
              </Typography>
            </ListItemIcon>
            <ListItemText 
              primary={language.nativeName}
              primaryTypographyProps={{
                variant: 'body2',
                sx: { fontWeight: language.code === currentLanguage ? 600 : 400 }
              }}
            />
            {language.code === currentLanguage && (
              <CheckIcon fontSize="small" color="primary" sx={{ ml: 1 }} />
            )}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default LanguageSwitcher;
