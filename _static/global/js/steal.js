let stealGameComponent = {
    components: {
        'police-log-component': policeLogComponent,
        'probability-bar-component': probabilityBarComponent,
    },
    props: {
        properties: Array,
        playerGroupId: String,
        playerLocation: Object,
        investigationCount: Number,
        probCulprit: Number,
        probInnocent: Number,
        policeLogMessages: Array,
        mapSize: Number,
    },
    data: function () {
        return {
            location: null,
            locationx: 0,
            locationy: 0,
        }
    },
    mounted: function () {
        // this.location = this.$refs.location todo: implement ref for location and all properties retreived by id
        let that = this;
        let selector = '#location'
        Draggable.create(selector, {
            minimumMovement: .01,
            bounds: document.getElementById("steal-container"), //todo add ref stuff
            snap: function (val) {
            },
            onDragStart: function () {
                that.locationDragStart(this)
            },
            onDragEnd: function () {
                that.checkLocation(this)
            },
        });
        // animate to start
        //   if (this.playerLocation && this.playerLocation.property !== null) {
        //     this.calculateLocation(property, 2);
        //
        //       let propertySelector = 'prop' + this.playerLocation.property
        //       let property = document.getElementById(propertySelector).getBoundingClientRect() //todo use refs
        //       let location = this.$refs.location.getBoundingClientRect()
        //       this.locationx = location.x - property.x
        //       this.locationy = location.y - property.y
        //
        //       gsap.to(selector, {left: this.playerLocation.x-15, top: this.playerLocation.y-10})
        //   }
    },
    methods: {
        locationDragStart: function (that) {
            // check the current location to see if we need to update api
            this.$emit('location-drag', {x: this.locationx, y: this.locationy, property: 0});
        },
        checkLocation: function (that) {
            if (that.hitTest(this.$refs.htarget, '10%')) {
                //location-center
                if (that.hitTest(this.$refs.prop2, '.000001%') && this.playerGroupId != 2) {
                    let property = document.getElementById('prop2').getBoundingClientRect()
                    this.calculateLocation(property, 2);
                } else if (that.hitTest(this.$refs.prop3, '.000001%') && this.playerGroupId != 3) {
                    let property = document.getElementById('prop3').getBoundingClientRect()
                    this.calculateLocation(property, 3);
                } else if (that.hitTest(this.$refs.prop4, '.000001%') && this.playerGroupId != 4) {
                    let property = document.getElementById('prop4').getBoundingClientRect()
                    this.calculateLocation(property, 4);
                } else if (that.hitTest(this.$refs.prop5, '.000001%') && this.playerGroupId != 5) {
                    let property = document.getElementById('prop5').getBoundingClientRect()
                    this.calculateLocation(property, 5);
                } else {
                    gsap.to('#location', .1, {fill: 'green'}) // todo what is this?
                    gsap.to('#location', 0.5, {x: 0, y: 0, ease: Back.easeOut});
                    this.$emit('location-token-reset')
                }
            } else {
                gsap.to('#location', 0.5, {x: 0, y: 0, ease: Back.easeOut});
                this.$emit('location-token-reset')
            }
        },
        calculateLocation(property, property_id) { // prop_id is more like the player_id
            let location = this.$refs.location.getBoundingClientRect()
            // console.log(this.$refs.location)
            // console.log(location)
            this.locationx = location.x - property.x + 2 - 1 // + radius - border
            this.locationy = location.y - property.y + 2 - 1

            if (0 <= this.locationx &&
                this.locationx <= this.mapSize &&
                0 <= this.locationy &&
                this.locationy <= this.mapSize
            ) {
                this.$emit('location-update', {x: this.locationx, y: this.locationy, property: property_id});
            } else {
                gsap.to('#location', 0.5, {x: 0, y: 0, ease: Back.easeOut});
            }
        },
        indicatorColor(property) {
            if (this.playerGroupId == property) {
                return 'red'
            }
            else {
                return 'black'
            }
        }
    },
    template:
        `
      <div class="steal" style="display:flex; flex-wrap: wrap">
        <div class="game">
            <div id="steal-container" class="upper">
                <div class='title'>Maps</div> 
                    <div ref='htarget' class="properties-container">
                      <div v-for="property in properties" class="property-container">
                            <div v-bind:class="['property', playerGroupId==(property+1) ? 'self' : 'other']" v-bind:player-id="(property+1)" :id='"prop" + (property+1)' :ref='"prop" + (property+1)'>
                                <!-- svg indicator id format: property-player-->
                                <svg v-for="player_id in 4" :key="player_id" :id="'indicator' + (property+1) + '-' + (player_id + 1)" class="indicator" width="4" height="4">
                                  <circle cx="3" cy="3" r="2" :fill="indicatorColor(player_id+1)" />
                                </svg>
                            </div>
                            <div class="property-label">{{property+1 == playerGroupId ? 'You' : 'Player ' + (property+1)}}</div>
                      </div>
                    </div>
                    <div class="token-container">
                      <div class="title-small">
                        Location Token:
                      </div>
                      <svg id="location" height="21" width="21">
                        <line x1="0" y1="0" x2="21" y2="21" style="stroke:red;stroke-width:3;"/>       
                        <line x1="21" y1="0" x2="0" y2="21" style="stroke:red;stroke-width:3;"/>       
                            
                        <circle ref="location" cx="10.5" cy="10.5" r="2" fill="black" />
                        Sorry, your browser does not support inline SVG.  
                      </svg> 
                      <br>
                      <div>
                        <div>DEBUG:</div>
                        player id: {{playerGroupId}} <br>
                        x: {{locationx}}<br> 
                        y: {{locationy}}<br>
                      </div>
                    </div>
              </div>
            <div class="lower" style="display:flex;">
                <police-log-component
                    class="notifications-container"
                    style="border-right: 1px solid black;"
                    :messages="policeLogMessages"
                ></police-log-component>
                <div class="investigation-data-container">
                    <div class="title">Investigation</div>
                    <div class="title-small">Defense Tokens: {{investigationCount}}/9</div>
                    <br>
                    <probability-bar-component label="Probability Punish Innocent" :percent=probInnocent></probability-bar-component>
                    <probability-bar-component label="Probability Punish Culprit" :percent=probCulprit></probability-bar-component>                    
                </div>
            </div>
        </div>
      </div>
      `
}