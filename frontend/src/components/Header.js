import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  Add as AddIcon,
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Storage as StorageIcon,
  Assignment as ProjectIcon
} from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './LanguageSwitcher';

const Header = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const location = useLocation();
  const [anchorEl, setAnchorEl] = React.useState(null);
  const [addMenuAnchorEl, setAddMenuAnchorEl] = React.useState(null);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleAddMenuOpen = (event) => {
    setAddMenuAnchorEl(event.currentTarget);
  };

  const handleAddMenuClose = () => {
    setAddMenuAnchorEl(null);
  };

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component={Link} to="/" sx={{
          flexGrow: 1,
          textDecoration: 'none',
          color: 'inherit',
          display: 'flex',
          alignItems: 'center'
        }}>
          MigrateIQ
        </Typography>

        {isMobile ? (
          <>
            <LanguageSwitcher />

            <IconButton
              color="inherit"
              aria-label="add new item"
              onClick={handleAddMenuOpen}
              sx={{ mr: 1 }}
            >
              <AddIcon />
            </IconButton>
            <Menu
              anchorEl={addMenuAnchorEl}
              open={Boolean(addMenuAnchorEl)}
              onClose={handleAddMenuClose}
            >
              <MenuItem
                component={Link}
                to="/projects/new"
                onClick={handleAddMenuClose}
              >
                {t('projects.newProject')}
              </MenuItem>
              <MenuItem
                component={Link}
                to="/data-sources/new"
                onClick={handleAddMenuClose}
              >
                {t('dataSources.newDataSource')}
              </MenuItem>
            </Menu>

            <IconButton
              color="inherit"
              aria-label="menu"
              onClick={handleMenuOpen}
            >
              <MenuIcon />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem
                component={Link}
                to="/"
                onClick={handleMenuClose}
                selected={isActive('/')}
              >
                {t('navigation.dashboard')}
              </MenuItem>
              <MenuItem
                component={Link}
                to="/projects"
                onClick={handleMenuClose}
                selected={isActive('/projects')}
              >
                {t('navigation.projects')}
              </MenuItem>
              <MenuItem
                component={Link}
                to="/data-sources"
                onClick={handleMenuClose}
                selected={isActive('/data-sources')}
              >
                {t('navigation.dataSources')}
              </MenuItem>
            </Menu>
          </>
        ) : (
          <>
            <Box>
              <Button
                color="inherit"
                component={Link}
                to="/"
                startIcon={<DashboardIcon />}
                sx={{
                  backgroundColor: isActive('/') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.2)'
                  }
                }}
              >
                {t('navigation.dashboard')}
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/projects"
                startIcon={<ProjectIcon />}
                sx={{
                  backgroundColor: isActive('/projects') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.2)'
                  }
                }}
              >
                {t('navigation.projects')}
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/data-sources"
                startIcon={<StorageIcon />}
                sx={{
                  backgroundColor: isActive('/data-sources') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.2)'
                  }
                }}
              >
                {t('navigation.dataSources')}
              </Button>
            </Box>

            <LanguageSwitcher variant="button" />

            <IconButton
              color="inherit"
              aria-label="add new item"
              onClick={handleAddMenuOpen}
              sx={{ ml: 2 }}
            >
              <AddIcon />
            </IconButton>
            <Menu
              anchorEl={addMenuAnchorEl}
              open={Boolean(addMenuAnchorEl)}
              onClose={handleAddMenuClose}
            >
              <MenuItem
                component={Link}
                to="/projects/new"
                onClick={handleAddMenuClose}
              >
                {t('projects.newProject')}
              </MenuItem>
              <MenuItem
                component={Link}
                to="/data-sources/new"
                onClick={handleAddMenuClose}
              >
                {t('dataSources.newDataSource')}
              </MenuItem>
            </Menu>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;
