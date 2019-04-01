import searchBar from './searchBar.js';
import React from 'react';
import PropTypes from 'prop-types';
import InputBase from '@material-ui/core/InputBase';
import { withStyles } from '@material-ui/core/styles';
import { Button } from '@material-ui/core';
import CFFlogo from './cff_logo.png';

const styles = theme => ({
  root: {
   width: '50%',
   display: 'flex',
   paddingTop: 10,
   paddingLeft: 15,
  },
  // title: {
  //   display: 'none',
  //   [theme.breakpoints.up('sm')]: {
  //     display: 'block',
  //   },
  logo: {
    display: 'block', 
    justifyContent:'left',
    alignItems:'left',
    margin: 30,
    margin: theme.spacing.unit,
    paddingLeft: 10,
    },
  //},

  button:{
    margin: theme.spacing.unit,
    padding: 10,
    paddingTop: 10,
    marginTop: 15,


  },

  search: {
    width: '200%',
    position: 'relative',
    borderRadius: 10, 
    borderWidth: 10,
    padding: 10, 
    margin: 30,
    marginLeft: 20,
    margin: theme.spacing.unit,
    backgroundColor: '#eeeeee',

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



function SearchBar2(props) {
  const { classes } = props;
  return (
    <div className={classes.root}>
          <div className={classes.logo}>
            <img
              src={CFFlogo} 
              alt="logo" width="100px"/>
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
            <Button variant="contained" component="span" className={classes.button}>
              Search
            </Button>
          </div>
    </div>
  );
}


SearchBar2.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(SearchBar2);