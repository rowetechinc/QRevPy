class UMeasurement(object):
    """Class to generate stacked bar graph of contributions to uncertainty.

    Attributes
    ----------
    canvas: MplCanvas
        Object of MplCanvas a FigureCanvas
    fig: Object
        Figure object of the canvas
    hover_connection: int
        Index to data cursor connection
    annot: Annotation
        Annotation object for data cursor
    """

    def __init__(self, canvas):
        """Initialize object using the specified canvas.

        Parameters
        ----------
        canvas: MplCanvas
            Object of MplCanvas
        """

        # Initialize attributes
        self.canvas = canvas
        self.fig = canvas.fig
        self.hover_connection = None
        self.annot = None
        self.col_labels = {'u_syst':'System', 'u_compass':'Compass', 'u_movbed':'Moving-bed', 'u_ens':'# Ensembles',
                           'u_meas':'Meas. Q', 'u_top':'Top Q', 'u_bot':'Bottom Q',
                           'u_left':'Left Q', 'u_right':'Right Q', 'u_boat':'Inv. Boat', 'u_depth':'Inv. Depth',
                           'u_water':'Inv. Water', 'u_cov':'COV'}
        self.plot_df_cumsum = None
        self.plot_df = None

    def create(self, oursin):
        """Create the axes and lines for the figure.

        Parameters
        ----------
        oursin: Oursin
            Object of Oursin uncertainty model
        """

        # Clear the plot
        self.fig.clear()

        # Configure axis
        self.fig.ax = self.fig.add_subplot(1, 1, 1)

        # Create dataframe to plot
        self.plot_df = oursin.u_contribution_measurement_user.drop(['total'], axis=1)
        self.plot_df = self.plot_df.append(oursin.u_contribution_user.drop(['total'], axis=1), ignore_index=True)
        self.plot_df = self.plot_df * 100

        # Create dataframe to use for data cursor
        self.plot_df_cumsum = self.plot_df.cumsum(axis='columns')

        # Create x tick labels
        x_tick_labels = ['All']
        for n in range(1, self.plot_df.shape[0]):
            x_tick_labels.append(str(n))

        # Create legend labels
        custom_labels = ['System', 'Compass', 'Moving-bed', '# Ensembles', 'Meas. Q', 'Top Q', 'Bottom Q',
                  'Left Q', 'Right Q', 'Inv. Boat', 'Inv. Depth', 'Inv. Water', 'COV']

        # Generate bar graph
        self.plot_df.plot(kind='bar', stacked=True, ax=self.fig.ax, legend=False)

        # Set margins and padding for figure
        self.fig.subplots_adjust(left=0.01, bottom=0.01, right=0.95, top=0.99, wspace=0, hspace=0)
        self.fig.ax.set_ylabel(self.canvas.tr('Percent of Total Uncertainty'))
        self.fig.ax.set_xlabel(self.canvas.tr('Transects'))
        self.fig.ax.set_xticklabels(x_tick_labels, rotation='horizontal', fontsize=12)
        self.fig.ax.xaxis.label.set_fontsize(12)
        self.fig.ax.yaxis.label.set_fontsize(12)
        self.fig.ax.tick_params(axis='both', direction='in', bottom=True, top=True, left=True, right=True)

        # Arrange legend in reverse order to match stacked bars
        handles, labels = self.fig.ax.get_legend_handles_labels()
        self.fig.ax.legend(reversed(handles), reversed(custom_labels), fontsize=12, loc='center left',
                           bbox_to_anchor=(1, 0.5))

        self.annot = self.fig.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                              bbox=dict(boxstyle="round", fc="w"),
                                              arrowprops=dict(arrowstyle="->"))

        self.annot.set_visible(False)

        self.canvas.draw()

    def update_annot(self, col_name, u_value, event):
        """Updates the location and text and makes visible the previously initialized and hidden annotation.

        Parameters
        ----------
        col_name: str
            Column name in data frame
        u_value: float
            Uncertainty percent
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Get selected data coordinates
        pos = [event.xdata, event.ydata]

        # Shift annotation box left or right depending on which half of the axis the pos x is located and the
        # direction of x increasing.
        if self.fig.ax.viewLim.intervalx[0] < self.fig.ax.viewLim.intervalx[1]:
            if pos[0] < (self.fig.ax.viewLim.intervalx[0] + self.fig.ax.viewLim.intervalx[1]) / 2:
                self.annot._x = -20
            else:
                self.annot._x = -80
        else:
            if pos[0] < (self.fig.ax.axes.viewLim.intervalx[0] + self.fig.ax.viewLim.intervalx[1]) / 2:
                self.annot._x = -80
            else:
                self.annot._x = -20

        # Shift annotation box up or down depending on which half of the axis the pos y is located and the
        # direction of y increasing.
        if self.fig.ax.viewLim.intervaly[0] < self.fig.ax.viewLim.intervaly[1]:
            if pos[1] > (self.fig.ax.viewLim.intervaly[0] + self.fig.ax.viewLim.intervaly[1]) / 2:
                self.annot._y = -40
            else:
                self.annot._y = 20
        else:
            if pos[1] > (self.fig.ax.viewLim.intervaly[0] + self.fig.ax.viewLim.intervaly[1]) / 2:
                self.annot._y = 20
            else:
                self.annot._y = -40

        self.annot.xy = pos

        # Format and display text
        text =  '{}: {:2.2f}'.format(self.col_labels[col_name], u_value)
        self.annot.set_text(text)

    def hover(self, event):
        """Determines if the user has selected a location with data and makes
        annotation visible and calls method to update the text of the annotation. If the
        location is not valid the existing annotation is hidden.

        Parameters
        ----------
        event: MouseEvent
            Triggered when mouse button is pressed.
        """

        # Set annotation to visible
        vis = self.annot.get_visible()

        # Determine if mouse location references a data point in the plot and update the annotation.
        if event.inaxes == self.fig.ax:
            row = int(round(event.xdata))
            df_row = self.plot_df_cumsum.iloc[row, :]
            col_name =df_row[df_row.gt(event.ydata)].index[0]
            u_value = self.plot_df.loc[row, col_name]

            self.update_annot(col_name, u_value, event)
            self.annot.set_visible(True)
            self.canvas.draw_idle()

        else:
            # If the cursor location is not associated with the plotted data hide the annotation.
            if vis:
                self.annot.set_visible(False)
                self.canvas.draw_idle()

    def set_hover_connection(self, setting):
        """Turns the connection to the mouse event on or off.

        Parameters
        ----------
        setting: bool
            Boolean to specify whether the connection for the mouse event is active or not.
        """

        if setting and self.hover_connection is None:
            self.hover_connection = self.canvas.mpl_connect('button_press_event', self.hover)
        elif not setting:
            self.canvas.mpl_disconnect(self.hover_connection)
            self.hover_connection = None
            self.annot.set_visible(False)
            self.canvas.draw_idle()