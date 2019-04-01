import React from 'react';
import PropTypes from 'prop-types';
import InputBase from '@material-ui/core/InputBase';
import { withStyles } from '@material-ui/core/styles';
import { Button } from '@material-ui/core';
import {Link} from 'react-router-dom';
import CFFlogo from './cff_logo.png';
import './App.js';


const styles = theme => ({
  root: {
   width: '30%', 
   margin: 'auto',
   paddingTop: 150,
  },
  logo: {
    display: 'flex', 
    justifyContent:'center',
    alignItems:'center',
    margin: 30,
  },
  search: {
    position: 'relative',
    borderRadius: 10, 
    borderWidth: 10,
    padding: 10, 
    margin: 10,
    backgroundColor: '#eeeeee',
    },
  button: {
    display:'flex',
    justifyContent:'center',
    alignItems:'center',
    padding: 10,
    margin: 20,
    margin: 'auto',
    width: '25%',
    
    },
  inputRoot: {
    color: 'inherit',
    width: '100%',
  },

  inputInput: {
    paddingTop: theme.spacing.unit,
    paddingRight: theme.spacing.unit,
    paddingBottom: theme.spacing.unit,
    paddingLeft: theme.spacing.unit,
    transition: theme.transitions.create('width'),
    [theme.breakpoints.up('sm')]: {
      '&:focus': {
      },
    },
  },
});

function SearchBar(props) {
  const { classes } = props;

    return (
    <div className={classes.root}>
          <div className={classes.logo}>
            <img
              src={CFFlogo} 
              alt="logo" width="230px"/>
          </div>
          <div className={classes.search}>
            <InputBase
              placeholder="Search…"
              fullWidth
              classes={{
                root: classes.inputRoot,
                input: classes.inputInput,
              }}
            />
          </div>
          <div>
            <Button variant="contained" component={Link} to="/App" className={classes.button}>
                Search
            </Button>
          </div>
    </div>
  );
}


SearchBar.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(SearchBar);
