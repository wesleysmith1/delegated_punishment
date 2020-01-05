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
  
  let officerUnitsComponent = {
    components: {
    },
    props: {
      officerUnits: Array,
    },
    data: function() {
      return {
        playerId: Number
      }
    },
    mounted: function() {
      for (var i = 0; i < this.officerUnits.length; i++) {
        let that = this;
        Draggable.create("#unit" + i, {
          bounds: document.getElementById("officerGame"), //todo add ref stuff
          onDragEnd: function() {
            that.checkLocation(this)
          },
          
        });
      }
    },
    methods: {
      checkLocation: function(that) {
        if(that.hitTest(this.$refs.officergame, '100%')){
          //location-center
          if(that.hitTest(this.$refs.prop1, '1%')) {
              let property = document.getElementById('prop1').getBoundingClientRect()
              this.calculateLocation(property);
          } else if (that.hitTest(this.$refs.prop2, '1%')) {
              let property = document.getElementById('prop2').getBoundingClientRect()
              this.calculateLocation(property);
          } else if (that.hitTest(this.$refs.prop3, '1%')) {
              let property = document.getElementById('prop3').getBoundingClientRect()
              this.calculateLocation(property);
          } else if (that.hitTest(this.$refs.prop4, '1%')) {
              let property = document.getElementById('prop4').getBoundingClientRect()
              this.calculateLocation(property);
          } else {
              // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
          }
          
        } else{
          // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
        }
      },
      calculateLocation(property) {
          let location = this.$refs.location.getBoundingClientRect()
          this.locationx = location.x - property.x
          this.locationy = location.y - property.y
      }
    },
    template: 
      `
        <div class="officer-units" style="display:flex; flex-wrap: flex;">
          <div v-for="(unit, index) in officerUnits" :id="'unit'+index" class="officer-unit" :ref='"unit" + unit'>
          </div>
        </div>
      `
  }
  
  let policeGameComponent = {
    components: {
      'police-log-component': policeLogComponent,
      'property-component': propertyComponent,
      'officer-units-component': officerUnitsComponent
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
        probPunishInnocent: 0,
        probPunishCulprit: 0,
      }
    },
    created: function() {
      this.locationx = '';
      this.locationy = '';
      this.property = '';   
    },
    mounted: function() {
      for (var i = 0; i < this.officerUnits.length; i++) {
        let that = this;
        Draggable.create("#unit" + i, {
          bounds: document.getElementById("officerGame"), //todo add ref stuff
          onDragEnd: function() {
            that.checkLocation(this)
          },
        });
      }
    },
    methods: {
      checkLocation: function(that) {
        if(that.hitTest(this.$refs.officergame, '100%')){
          //location-center
          if(that.hitTest(this.$refs.prop1, '1%')) {
            this.property = 1
              let property = document.getElementById('prop1').getBoundingClientRect()
              this.calculateLocation(property, that);
          } else if (that.hitTest(this.$refs.prop2, '1%')) {
            this.property = 2
              let property = document.getElementById('prop2').getBoundingClientRect()
              this.calculateLocation(property, that);
          } else if (that.hitTest(this.$refs.prop3, '1%')) {
            this.property = 3
              let property = document.getElementById('prop3').getBoundingClientRect()
              this.calculateLocation(property, that);
          } else if (that.hitTest(this.$refs.prop4, '1%')) {
            this.property = 4
              let property = document.getElementById('prop4').getBoundingClientRect()
              this.calculateLocation(property, that);
          } else if (that.hitTest(this.$refs.detectivecontainer, '100%')) {
            this.probPunishCulprit = this.probPunishCulprit + 10
          } else {
              // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
          }
        } else{
          // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
        }
      },
      calculateLocation(property, unitContext) {
        if (this.probPunishInnocent< 100 ) this.probPunishInnocent = this.probPunishInnocent + 10;
          let unit = unitContext.target.getBoundingClientRect()
          this.locationx = unit.x - property.x
          this.locationy = unit.y - property.y
      }
    },
    template: 
      `
        <div class="officer" style="display:flex;">
          <div class="game" ref="officergame">
              <div class="upper">             
                <div style="display: flex">
                  <div class="property" v-for="property in properties" v-bind:player-id="property" :id='"prop" + property' :ref='"prop" + property'>
                    {{property}}
                  </div>
                </div>
                <div class="officer-units" style="display:flex;">
                  <div v-for="(unit, index) in officerUnits" :id="'unit'+index" class="officer-unit" :ref='"unit" + unit'>
                  </div>
                </div>
                <div style="margin: 10px">
                  last dropped<br>
                  property: {{property}}<br>
                  x: {{locationx}}<br>
                  y: {{locationy}}<br>
                </div>
              </div>
              <div class="lower" style="display:flex;">
                <police-log-component></police-log-component>
                <div class="officer-data">
                  Punishment Map
                  <div id="officer-detective-container" ref='detectivecontainer'></div>
  
                  Probability Punish Innocent {{probPunishInnocent}} / 100
                  <div class='bar'>
                    <div class="innocent" :style="{'width':(probPunishInnocent+'%')}">
                    </div>
                  </div>
                  Probability Punish Culprit {{probPunishCulprit}} / 100
                  <div class='bar'>
                    <div class="culprit" :style="{'width':(probPunishCulprit+'%')}">
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