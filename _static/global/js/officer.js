let buttonLocationComponent = {
    props: { location: Object,},
    template: '<div><button type="button"">{{location.name}}</button></div>'
  }
  
  let propertyComponent = {
    props: { playerId: Number,},
    template: "<div class='property' ref='prop1'>{{playerId}}</div>"
  }
    
  let policeLogComponent = {
    props: { items: Array,},
    data: function () {
        return {
        }
    },
    template: '<div class="police-log">POLICE LOG PLACEHOLDER</div>'
  }

  let policeGameComponent = {
    components: {
      'police-log-component': policeLogComponent,
      'property-component': propertyComponent,
    },
    props: {
      properties: Array,
      officerUnits: Array,
      playerGroupId: String,
    },
    data: function() {
      return {
        playerId: Number,
        locationx: String,
        locationy: String,
        property: String,
        investigationTokens: 0,
        probPunishInnocent: 0,
        probPunishCulprit: 0,
      }
    },
    created: function() {
      this.locationx = '';
      this.locationy = '';
      this.property = '';
      //todo: load investigation tokens from api
      this.investigationTokens = 0;
    },
    mounted: function() {
      for (let i = 0; i < this.officerUnits.length; i++) {
        let that = this;
        let drag = Draggable.create("#unit" + i, {
          zIndexBoost: false,
          bounds: document.getElementById("officerGame"), //todo add ref stuff
          onDragStart: function() {
            that.tokenDragStart(this, that.officerUnits[i])
          },
          onDragEnd: function () {
            that.checkLocation(this, that.officerUnits[i])
          },
        });
        drag.zIndex = 500;
      }
    },
    methods: {
      tokenDragStart: function(that, item) {
        console.log('DRAGGING TOKEN')
        // this.property = 0
        // item.property = 0
        // item.x = -100
        // item.y = -100
        //
        // // update api with unit location
        // this.updateOfficerToken(item);
      },
      checkLocation: function (that, item) {
        if (that.hitTest(this.$refs.officergame, '100%')) {
          //location-center
          if (that.hitTest(this.$refs.prop5, '1%')) {
            this.property = 5
            item.property = 5;
            let property = document.getElementById('prop5').getBoundingClientRect()
            this.calculateLocation(property, that, item);
          } else if (that.hitTest(this.$refs.prop2, '1%')) {
            this.property = 2
            item.property = 2;
            let property = document.getElementById('prop2').getBoundingClientRect()
            this.calculateLocation(property, that, item);
          } else if (that.hitTest(this.$refs.prop3, '1%')) {
            this.property = 3
            item.property = 3
            let property = document.getElementById('prop3').getBoundingClientRect()
            this.calculateLocation(property, that, item);
          } else if (that.hitTest(this.$refs.prop4, '1%')) {
            this.property = 4
            item.property = 4
            let property = document.getElementById('prop4').getBoundingClientRect()
            this.calculateLocation(property, that, item);
          } else if (that.hitTest(this.$refs.detectivecontainer, '100%')) {
            this.investigationTokens++;
            this.probPunishCulprit = 1/3+2*(this.investigationTokens)/30
            this.probPunishInnocent = 1/3-(this.investigationTokens)/30
            item.property = 11
            this.updateOfficerToken(item)
          } else {
            gsap.to(that.target, 0.5, {x: 0, y: 0, ease: Back.easeOut});
          }
        } else {
          gsap.to(that.target, 0.5, {x: 0, y: 0, ease: Back.easeOut});
        }
      },
      calculateLocation(property, unitContext, item) { // todo: how is the function even working? make it: calculateLocation: function() {}
        if (this.probPunishInnocent < 100) this.probPunishInnocent = this.probPunishInnocent + 10; //todo fix this logic

        let unit = unitContext.target.getBoundingClientRect()
        this.locationx = unit.x - property.x;
        this.locationy = unit.y - property.y;
        item.x = this.locationx;
        item.y = this.locationy;
        // item.property =
        // update api with unit location
        this.updateOfficerToken(item);
      },
      updateOfficerToken(item) {
        // todo: send event up
        console.log('item: ', item);
        this.$emit('token-update', item);
      }
    },
    template: 
      `
        <div class="officer" style="display:flex;">
          <div class="game" ref="officergame">
              <div class="upper">             
                <div style="display: flex; justify-content: space-between;">
                  <div class="property other" v-for="property in properties" v-bind:player-id="(property+1)" :id='"prop" + (property+1)' :ref='"prop" + (property+1)'>
                    {{property+1}}
                    <!-- svg indicator id format: property-player-->
                    <svg v-for="player_id in 4" :key="player_id" :id="'indicator' + (property+1) + '-' + (player_id + 1)" class="indicator" width="6" height="6">
                      <circle cx="3" cy="3" r="3" fill="black" />
                    </svg>
                  </div>
                </div>
                <div class="officer-units" style="display:flex;">
                  <div v-for="(unit, index) in officerUnits" :id="'unit'+index" class="officer-unit" :ref='"unit" + unit'>
                    {{unit.number}}
                  </div>
                </div>
                <div style="margin: 10px">
                <div>DEBUG:</div>
                  last dropped<br>
                  property: {{property}}<br>
                  x: {{locationx}}<br>
                  y: {{locationy}}<br>
                </div>
              </div>
              <div class="lower" style="display:flex;">
                <police-log-component></police-log-component>
                <div class="officer-data">
                  <h3>Investgation</h3>
                    <div>
                      DEBUG: Investigation Token Count {{investigationTokens}} <br>  
                    </div>
                  <div id="officer-detective-container" ref='detectivecontainer'></div>
  
                  Probability Punish Innocent {{probPunishInnocent}}
                  <div class='bar'>
                    <div class="innocent" :style="{'width':(probPunishInnocent*100+'%')}">
                    </div>
                  </div>
                  Probability Punish Culprit {{probPunishCulprit}}
                  <div class='bar'>
                    <div class="culprit" :style="{'width':(probPunishCulprit*100+'%')}">
                    </div>
                  </div>
                  
                </div>
              </div>
          </div>
        </div>
      `
  }
  
  let playerHouseComponent = {
    props: { player: Object,},
    data: function () {
        return {
        }
    },
    template: '<div class="house">player"s house</div>'
  }