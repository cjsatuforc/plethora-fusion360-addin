<template>
  <div class="log-in">
    <h1>LOG IN</h1>
    <div v-if="errorMessage !== ''" class="alert">
      <p>{{ errorMessage }}</p>
    </div>
    <input v-if="!loading" type="email" name="email" v-model="input.email" placeholder="Email" />
    <input v-if="!loading" type="password" name="password" v-model="input.password" placeholder="Password" />
    <button class="plethora-button" v-if="!loading" type="button" v-on:click="logIn()">
      Log In
      <img src="../assets/arrow-cta.svg" />
    </button>
    <vue-simple-spinner size="medium" line-fg-color="#51ca7a" v-if="loading"></vue-simple-spinner>
  </div>
</template>

<script>
export default {
  name: "LogIn",
  data: function() {
    return {
      input: {
        email: "",
        password: ""
      },
      errorMessage: "",
      loading: false
    };
  },
  mounted() {
    this.$eventBus.$on("login", data => {
      this.loading = false;
      if (data.success === true) {
        this.$router.replace({ name: "analyze" });
      } else if (data.error) {
        this.errorMessage = data.error;
      }
    });
  },
  methods: {
    logIn() {
      this.errorMessage = "";
      this.loading = true;

      var args = {
        email: this.input.email,
        password: this.input.password
      };
      if (typeof adsk !== "undefined") {
        // eslint-disable-next-line
        adsk.fusionSendData("login", JSON.stringify(args));
      } else {
        setTimeout(() => {
          this.$eventBus.$emit("login", {
            success: true,
            error: null
          });
        }, 2000);
      }
    }
  }
};
</script>

<style scoped>
input {
  display: block;
  width: 100%;
  font-size: 14px;
  font-weight: 300;
  background: rgba(0, 0, 0, 0);
  outline: none;
  border: none;
  border-bottom: 1px solid #9b9b9b;
  letter-spacing: 0.1em;
  margin: 0 0 36px 0;
  padding: 0.6em;
  box-sizing: border-box;
}
</style>

