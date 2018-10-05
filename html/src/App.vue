<template>
  <div id="app">
    <div class="nav">
      <div class="container">
        <img class="nav-logo" src="./assets/logo-black.svg" />
      </div>
    </div>
    <router-link v-if="authenticated" to="/login" v-on:click.native="logout()" replace>Logout</router-link>
    <div class="container">
      <router-view @authenticated="setAuthenticated"></router-view>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      authenticated: false
    };
  },
  mounted() {
    if (!this.authenticated) {
      this.$router.replace({ name: "login" });
    }
  },
  methods: {
    setAuthenticated(status) {
      this.authenticated = status;
    },
    logout() {
      this.authenticated = false;
    }
  }
};
</script>


<style>
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans",
    "Helvetica Neue", sans-serif;
  margin: 0;
  background: white;
  color: #2f2f2f;
}

.nav {
  height: 50px;
  width: 100%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.nav-logo {
  width: 150px;
}

.container {
  padding-left: 20px;
  padding-right: 20px;
  padding-bottom: 20px;
}

h1 {
  font-size: 14px;
  font-weight: 200;
  margin-top: 20px;
  margin-bottom: 20px;
  letter-spacing: 0.15em;
}

p {
  font-weight: 400;
  font-size: 14px;
}

a {
  font-weight: 400;
  font-size: 14px;
  text-decoration: underline;
  color: #2f2f2f;
}

.alert {
  color: #ed1c24;
  padding: 0.6em;
}

.plethora-button {
  height: 60px;
  font-size: 16px;
  font-weight: 500;
  background-color: #51ca7a;
  display: block;
  letter-spacing: 0.01em;
  line-height: 24px;
  padding: 0 40px;
  border: none;
  cursor: pointer;
  margin-top: 10px;
  margin-bottom: 10px;
}
.plethora-button:hover {
  background-color: #46d678;
}
.plethora-button:active {
  color: #2f2f2f;
}
.plethora-button > img {
  margin-left: 13px;
  height: 11px;
}

.plethora-issue-list-item {
  font-weight: 400;
  font-size: 14px;
  line-height: 16px;
  list-style-image: none;
  list-style-position: outside;
  list-style-type: none;
  padding-left: 20px;
  padding-right: 10px;
  padding-top: 10px;
  padding-bottom: 10px;
}

.plethora-issue-list-item:hover {
  background-color: #fff903;
  cursor: pointer;
}

.plethora-checkbox {
  background-color: rgba(0, 0, 0, 0);
  background-size: 12px;
  border: none;
  outline: none;
  width: 12px;
  height: 12px;
}
.plethora-checkbox-empty {
  background-image: url("assets/check-empty.png");
}
.plethora-checkbox-checked {
  background-image: url("assets/check-checked.png");
}
.plethora-checkbox-mixed {
  background-image: url("assets/check-mixed.png");
}

.flex-display {
  display: flex;
}
.flex-center-items {
  align-items: center;
}
.flex-stretch {
  flex: 1 1 auto;
}
.flex-shrink {
  flex: 0 0 auto;
}

.strong {
  font-weight: 600;
}

.bp-dropdown__btn {
  font-size: 12px;
  border: 1px solid #acacac;
  width: 100%;
  box-sizing: border-box;
  padding: 10px !important;
}
.bp-dropdown__btn > img {
  width: 15px;
  margin-left: auto;
}
.bp-dropdown__body {
  padding: 0 !important;
  margin: 0;
  overflow: scroll;
  max-height: 200px;
}
.bp-dropdown__body > div {
  cursor: pointer;
  padding: 10px;
  font-size: 12px;
}
.bp-dropdown__body > div:hover {
  background-color: #fff903;
}
.ship-date-bp__body {
  max-height: 150px;
}

#app {
  text-align: left;
}
</style>

