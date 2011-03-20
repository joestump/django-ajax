/**
 * Todo: Add a client here.
 */

var client = {
    app: function(app) {
        this.app_ = app;
        return this;
    },
    model: function(model) {
        this.model_ = model;
        return this;
    },
    get: function(id) {
        console.log(this.app_, this.model_, id);
    }
};
